import pytest
from app.tasks.models.dummy_api import DummyAPIFlakyTask
from app.tasks.input_validation import InvalidTaskInputsError, parse_task_inputs


def test_dummy_flaky_task_input_validation():
    """
    Test the input validation for the DummyAPIFlakyTask.
    """
    raw_values = parse_task_inputs(
        [1, 2, 3], data_source="dummy-api", task_type="flaky"
    )


def test_dummy_flaky_task_input_validation_invalid():
    """
    Test the input validation for the DummyAPIFlakyTask with invalid inputs.

    One of the inputs is invalid (non-positive integer).
    """
    with pytest.raises(InvalidTaskInputsError):
        parse_task_inputs([0, 1, 2], data_source="dummy-api", task_type="flaky")
