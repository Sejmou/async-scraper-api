<script lang="ts">
	import type { DuckDBAPI, QueryResultRowMajor } from '$lib/duckdb.svelte';
	import DataTableExternalPagination from '$lib/components/ui/data-table-external-pagination.svelte';
	import { type OnChangeFn, type PaginationState } from '@tanstack/table-core';

	let { db, tableName }: { tableName: string; db: DuckDBAPI } = $props();

	let pagination: PaginationState = $state({
		pageIndex: 0,
		pageSize: 10
	});
	let offset = $derived(pagination.pageIndex * pagination.pageSize);

	const handlePaginationChange: OnChangeFn<PaginationState> = (updater) => {
		if (typeof updater === 'function') {
			pagination = updater(pagination);
		} else {
			pagination = updater;
		}
	};

	type ChunkData = { dataQueryRes: QueryResultRowMajor; totalRowCount: number };

	$effect(() => {
		async function fetchChunkData(): Promise<ChunkData> {
			const [chunkQueryRes, totalRowCount] = await Promise.all([
				db
					.executeQueryRowMajor(
						`SELECT * FROM ${tableName} LIMIT ${pagination.pageSize} OFFSET ${offset}`
					)
					.then((out) => {
						if (out.type === 'result') {
							return out;
						}
						console.error('Error fetching table chunk', out.error);
						throw out.error;
					}),
				db.getRowCount(tableName)
			]);
			return { dataQueryRes: chunkQueryRes, totalRowCount };
		}
		fetchChunkData().then((data) => (chunkData = data));
	});

	let chunkData: ChunkData | null = $state(null);
</script>

<!-- TanStack table (used by DataTableExternalPagination under the hood) is not able to respond to column/schema changes
 Need to use the key expression to rerender the table if the result columns array changes -->
{#if chunkData}
	{@const columns = chunkData.dataQueryRes.columns.map((col) => ({
		accessorKey: col,
		header: col
	}))}
	<DataTableExternalPagination
		{columns}
		{pagination}
		data={chunkData.dataQueryRes.data}
		rowCount={chunkData.totalRowCount}
		onPaginationChange={handlePaginationChange}
	/>
{/if}
