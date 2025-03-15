<script lang="ts">
	import type { DuckDBAPI, QueryOutputRowMajor } from '$lib/duckdb.svelte';
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

	$effect(() => {
		db.executeQueryRowMajor(
			`SELECT * FROM ${tableName} LIMIT ${pagination.pageSize} OFFSET ${offset}`
		).then((out) => (queryOutput = out));
	});

	let queryOutput: QueryOutputRowMajor | null = $state(null);
</script>

<!-- TanStack table (used by DataTableExternalPagination under the hood) is not able to respond to column/schema changes
 Need to use the key expression to rerender the table if the result columns array changes -->
{#if queryOutput && queryOutput.type === 'result'}
	{@const data = queryOutput.data}
	{@const columns = queryOutput.columns.map((col) => ({ accessorKey: col, header: col }))}
	{#key columns}
		<DataTableExternalPagination
			{columns}
			{data}
			rowCount={data.length}
			onPaginationChange={handlePaginationChange}
		/>
	{/key}
{/if}
