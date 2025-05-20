import tempfile
from typing import Sequence
import pytest
from dateutil import parser
from datetime import datetime, timezone

from app.tasks.queue_item_management import (
    TaskQueueItemManager,
    FatalProcessingError,
)


def get_seconds_since(dt: datetime) -> int:
    now = datetime.now(timezone.utc)
    delta = now - dt
    return int(delta.total_seconds())


def assert_is_valid_queue_item(output_item, input_item):
    assert isinstance(output_item, dict)
    assert "id" in output_item
    assert isinstance(output_item["id"], int)
    assert "data" in output_item
    data = output_item["data"]
    assert data == input_item
    assert "added_at" in output_item
    dt = parser.parse(output_item["added_at"])
    dt = dt.replace(tzinfo=timezone.utc)  # force UTC
    assert get_seconds_since(dt) < 5


def assert_queue_items_output_plausible(output, expected_items_data: list):
    assert isinstance(output, dict)
    assert "items" in output
    assert "total" in output
    assert "next_cursor" in output
    output_items = output["items"]
    assert isinstance(output_items, list)
    for input_item, output_item in zip(expected_items_data, output_items):
        assert_is_valid_queue_item(output_item=output_item, input_item=input_item)


@pytest.fixture
def temp_db_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.mark.asyncio
async def test_task_queue_processing_one_by_one(temp_db_dir):
    item_man = TaskQueueItemManager(
        db_dir=temp_db_dir,
        task_id=1,
    )

    async def dummy_single_int_processing_fn(x: int) -> str | None:
        if x == 2:
            return None
        if x == 3:
            raise Exception("Dummy error")
        if x == 4:
            raise FatalProcessingError("Dummy fatal error")
        return f"Processed {x}"

    await item_man.add_inputs([1, 2, 3, 4])

    try:
        while item_man.remaining_input_count > 0:
            await item_man.process_next_input_item(
                dummy_single_int_processing_fn,
                lambda input_item, output: print(f"Success: {input_item} -> {output}"),
                lambda x: print(f"No data returned for {x}"),
                lambda x, exc: print(f"Error processing {x}: {exc}"),
            )
    except FatalProcessingError:
        print("Fatal error occurred, stopping processing.")

    counts = item_man.queue_item_counts
    print(counts)

    assert counts["successes"] == 1
    assert counts["failures"] == 1
    assert counts["inputs_without_output"] == 1
    assert counts["remaining"] == 1


@pytest.mark.asyncio
async def test_task_queue_processing_batched(temp_db_dir):
    item_man = TaskQueueItemManager(
        db_dir=temp_db_dir,
        task_id=1,
    )

    await item_man.add_inputs([i + 1 for i in range(7)])

    async def dummy_batch_processing_fn(x: Sequence[int]) -> Sequence[str | None]:
        if 4 in x:
            raise Exception("Non-fatal dummy error")
        if 7 in x:
            raise FatalProcessingError("Fatal dummy error")
        return [f"Processed {i}" if i % 2 != 0 else None for i in x]

    completed_calls = 0

    try:
        while item_man.remaining_input_count > 0:
            await item_man.process_next_input_item_chunk(
                dummy_batch_processing_fn,
                chunk_size=3,
                on_success=lambda input_item, output: print(
                    f"Success: {input_item} -> {output}"
                ),
                on_no_data_returned=lambda x: print(f"No data returned for {x}"),
                on_non_fatal_error=lambda x, exc: print(f"Error processing {x}: {exc}"),
            )
            completed_calls += 1
    except FatalProcessingError:
        print("Fatal error occurred, stopping processing.")

    counts = item_man.queue_item_counts
    print(counts)

    assert completed_calls == 2
    assert counts["successes"] == 2
    assert counts["failures"] == 3
    assert counts["inputs_without_output"] == 1
    assert counts["remaining"] == 1

    assert_queue_items_output_plausible(item_man.get_queue_items("successes"), [1, 3])
    assert_queue_items_output_plausible(
        item_man.get_queue_items("inputs-without-output"), [2]
    )
    assert_queue_items_output_plausible(item_man.get_queue_items("failures"), [4, 5, 6])
    assert_queue_items_output_plausible(item_man.get_queue_items("inputs"), [7])
