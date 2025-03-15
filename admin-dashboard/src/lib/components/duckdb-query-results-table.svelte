<script lang="ts">
	import type { QueryResultRowMajor } from '$lib/duckdb.svelte';
	import DataTable from './ui/data-table.svelte';

	let { queryResults }: { queryResults: QueryResultRowMajor } = $props();
	let columns = $derived(
		queryResults.columns.map((col) => ({
			accessorKey: col,
			header: col
		}))
	);
	$inspect(columns);
	$inspect(queryResults);
</script>

<!-- TanStack table (used by DataTable under the hood) is not able to respond to column/schema changes
 Need to use the key expression to rerender the table if the result columns array changes -->
{#key queryResults.columns}
	<DataTable {columns} data={queryResults.data} />
{/key}
