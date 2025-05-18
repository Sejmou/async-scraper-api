import tempfile
from typing import Sequence
import pytest

from app.tasks.queue_item_management import TaskQueueItemManager, FatalProcessingError


@pytest.fixture
def temp_db_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.mark.asyncio
async def test_task_queue_processing_one_by_one(temp_db_dir):
    item_man = TaskQueueItemManager(
        db_dir=temp_db_dir,
        input_item_cls=int,
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
        input_item_cls=int,
        task_id=1,
    )

    await item_man.add_inputs([1, 2, 3, 4])

    async def dummy_batch_processing_fn(x: Sequence[int]) -> Sequence[str | None]:
        if 4 in x:
            raise Exception("Non-fatal dummy error")
        if 7 in x:
            raise FatalProcessingError("Fatal dummy error")
        return [f"Processed {i}" if i % 2 != 0 else None for i in x]

    calls_made = 0

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
            calls_made += 1
    except FatalProcessingError:
        print("Fatal error occurred, stopping processing.")

    counts = item_man.queue_item_counts
    print(counts)

    assert counts["successes"] == 2
    assert item_man.get_queue_items("successes") == [1, 3]
    assert counts["inputs_without_output"] == 1
    assert item_man.get_queue_items("inputs-without-output") == [2]
    assert counts["failures"] == 3
    assert item_man.get_queue_items("failures") == [4, 5, 6]
    assert counts["remaining"] == 1
    assert item_man.get_queue_items("remaining-inputs") == [7]
    assert calls_made == 3
