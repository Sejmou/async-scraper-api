import tempfile
from typing import Sequence
import pytest
from dateutil import parser
from datetime import datetime, timezone

from app.tasks.queue_item_management import (
    QueueItemData,
    TaskQueueItemManager,
    FatalProcessingError,
)


async def handle_success(input_item: int, output: str | None):
    print(f"Success: {input_item} -> {output}")


async def handle_no_data(input_item: int):
    print(f"No data returned for {input_item}")


async def handle_error(input_item: int, exc: Exception):
    print(f"Error processing {input_item}: {exc}")


def get_seconds_since(dt: datetime) -> int:
    now = datetime.now(timezone.utc)
    delta = now - dt
    return int(delta.total_seconds())


def parse_date_string_assume_utc(string: str) -> datetime:
    dt = parser.parse(string)
    dt = dt.replace(tzinfo=timezone.utc)  # force UTC
    return dt


def assert_queue_items_query_items_plausible(
    items: list[QueueItemData],
    expected_values: Sequence,
):
    assert len(items) == len(expected_values)
    for output, expected_value in zip(items, expected_values):
        assert output.data == expected_value
        assert get_seconds_since(parse_date_string_assume_utc(output.added_at)) < 5


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

    item_man.add_inputs([1, 2, 3, 4])

    try:
        while item_man.remaining_input_count > 0:
            await item_man.process_next_input_item(
                dummy_single_int_processing_fn,
                on_success=handle_success,
                on_no_data_returned=handle_no_data,
                on_non_fatal_error=handle_error,
            )
    except FatalProcessingError:
        print("Fatal error occurred, stopping processing.")

    counts = item_man.queue_item_counts
    print(counts)

    assert counts.successes == 1
    assert counts.failures == 1
    assert counts.inputs_without_output == 1
    assert counts.remaining == 1


@pytest.mark.asyncio
async def test_task_queue_processing_batched(temp_db_dir):
    item_man = TaskQueueItemManager(
        db_dir=temp_db_dir,
        task_id=1,
    )

    item_man.add_inputs([i + 1 for i in range(7)])

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
                on_success=handle_success,
                on_no_data_returned=handle_no_data,
                on_non_fatal_error=handle_error,
            )
            completed_calls += 1
    except FatalProcessingError:
        print("Fatal error occurred, stopping processing.")

    counts = item_man.queue_item_counts
    print(counts)

    assert completed_calls == 2
    assert counts.successes == 2
    assert counts.failures == 3
    assert counts.inputs_without_output == 1
    assert counts.remaining == 1

    successes_res = item_man.get_queue_items("successes")
    assert_queue_items_query_items_plausible(successes_res.items, [1, 3])

    no_data_res = item_man.get_queue_items("inputs-without-output")
    assert_queue_items_query_items_plausible(no_data_res.items, [2])

    failures_res = item_man.get_queue_items("failures")
    assert_queue_items_query_items_plausible(failures_res.items, [4, 5, 6])

    remaining_res = item_man.get_queue_items("inputs")
    assert_queue_items_query_items_plausible(remaining_res.items, [7])
