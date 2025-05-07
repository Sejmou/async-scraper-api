<script lang="ts">
	import { createInfiniteQuery } from '@tanstack/svelte-query';
	import type { TaskQueueType } from '$lib/types-and-schemas/tasks/common';
	import { fetchTaskQueueItems } from '$lib/client-api/scrapers/tasks/queue-items';
	import * as Table from '$lib/components/ui/table';
	import { Button } from '$lib/components/ui/button';

	let {
		scraperId,
		scraperTaskId,
		queueType,
		onTotalChange
	}: {
		scraperId: number;
		scraperTaskId: number;
		queueType: TaskQueueType;
		onTotalChange: (newTotal: number) => void;
	} = $props();

	// this is workaround I added because calling onTotalChange directly inside queryFn of createInfiniteQuery didn't work - not sure why
	let updateTotal = $derived((newTotal: number) => onTotalChange(newTotal));

	let query = createInfiniteQuery({
		queryKey: [scraperId, scraperTaskId, 'queue-items', queueType],
		queryFn: ({ pageParam }) =>
			fetchTaskQueueItems(scraperId, scraperTaskId, queueType, pageParam).then((result) => {
				if (result.status === 'success') updateTotal(result.data.total);
				return result;
			}),
		initialPageParam: 0,
		getNextPageParam: (lastPage) => {
			if (lastPage.status === 'success' && lastPage.data.next_cursor) {
				return lastPage.data.next_cursor;
			}
			return undefined;
		}
	});

	let successPages = $derived.by(() => {
		const data = $query.data;
		if (!data) return [];
		return data.pages.filter((page) => page.status === 'success').map((page) => page.data);
	});

	let hasErrorPage = $derived.by(() => {
		const data = $query.data;
		if (!data) return false;
		return data.pages.some((page) => page.status === 'error');
	});
</script>

{#if $query.isPending}
	Loading...
{/if}
{#if $query.error}
	<span>Error: {$query.error.message}</span>
{/if}
{#if $query.isSuccess}
	{#if hasErrorPage}
		Some pages have errors. Please check the logs for more details.
	{:else}
		{#if successPages.length > 0 && successPages[0].items.length > 0}
			<div class="max-h-[520px] overflow-y-auto rounded-lg border">
				<Table.Root>
					<Table.Header>
						<Table.Row>
							<Table.Head>ID</Table.Head>
							<Table.Head>Data</Table.Head>
							<Table.Head>Added At</Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each successPages as page}
							{#each page.items as item}
								{@const { id, data, added_at } = item}
								<Table.Row>
									<Table.Cell>{id}</Table.Cell>
									<Table.Cell>{data}</Table.Cell>
									<Table.Cell>{added_at}</Table.Cell>
								</Table.Row>
							{/each}
						{/each}
					</Table.Body>
				</Table.Root>
			</div>
		{/if}
		<div class="mt-2 flex w-full flex-col items-center">
			<Button
				variant="outline"
				onclick={() => $query.fetchNextPage()}
				disabled={!$query.hasNextPage || $query.isFetchingNextPage}
			>
				{#if $query.isFetching}
					Loading more...
				{:else if $query.hasNextPage}
					Load More
				{:else}Nothing more to load{/if}
			</Button>
		</div>
	{/if}
{/if}
