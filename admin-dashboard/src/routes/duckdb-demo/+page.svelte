<script lang="ts">
	import DuckDBConsole from '$lib/components/duckdb/duckdb-console.client.svelte';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import { getDuckDB } from '$lib/duckdb.svelte';
	const duckDB = getDuckDB();
</script>

<PageHeading heading="DuckDB Demo" text="A demonstration of DuckDB WASM." />
{#if duckDB.value.state === 'ready'}
	<DuckDBConsole db={duckDB.value.db} />
{:else}
	<p>loading...</p>
{/if}
