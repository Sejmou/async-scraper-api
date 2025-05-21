from typing import Any, Literal, TypedDict
from pydantic import ValidationError

from app.db.models import DataSource
from app.tasks.models import TaskModel


class InputErrorDetails(TypedDict):
    index: int
    message: str


class InvalidTaskInputsError(Exception):
    """
    Exception raised when task inputs are invalid (i.e. could not be parsed into a valid TaskInputs instance).
    """

    def __init__(
        self,
        message: str,
        code: Literal["invalid-items", "unknown-data-source-or-task-type", "other"],
        invalid_inputs: list[InputErrorDetails] = [],
    ):
        super().__init__(message)
        self.code = code
        self.invalid_inputs = invalid_inputs


def parse_task_inputs(inputs: list[Any], data_source: DataSource, task_type: str):
    """
    Parse an arbitrary value into validated task inputs, raising an exception if that fails.

    Args:
        data: The data to be parsed.

    Returns:
        TaskInputs: The parsed task inputs.

    Raises:
        ValueError: If the data cannot be parsed into a valid task
    """
    try:
        value = TaskModel.model_validate(
            {
                "inputs": inputs,
                "task_type": task_type,
                "data_source": data_source,
            }
        )
        return value.root.inputs
    except ValidationError as e:
        error_details: list[InputErrorDetails] = []
        for error in e.errors():
            if error["type"] == "union_tag_invalid":
                task_type = error["input"].get("task_type")
                data_source = error["input"].get("data_source")
                raise InvalidTaskInputsError(
                    f'Combination of data_source "{data_source}" and task_type "{task_type}" is invalid (or not supported yet)',
                    code="unknown-data-source-or-task-type",
                )

            loc = error["loc"]
            if len(loc) != 4 or loc[0] != "inputs" or loc[2] != "inputs":
                raise InvalidTaskInputsError(
                    f"Invalid task inputs: {error['msg']}",
                    code="other",
                ) from e
            invalid_input_idx = loc[3]
            if not isinstance(invalid_input_idx, int):
                raise InvalidTaskInputsError(
                    f"Invalid task inputs: {error['msg']}",
                    code="other",
                ) from e

            error_details.append(
                {
                    "index": invalid_input_idx,
                    "message": error["msg"],
                }
            )

        if len(error_details) != len(inputs):
            raise InvalidTaskInputsError(
                f"{len(error_details)} inputs were invalid and some other unexpected error(s) occurred, check server logs for details",
                code="invalid-items",
            ) from e

        raise InvalidTaskInputsError(
            f"{len(error_details)} inputs were invalid",
            code="invalid-items",
            invalid_inputs=error_details,
        )
