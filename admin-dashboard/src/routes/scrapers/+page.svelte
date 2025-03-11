<script lang="ts">
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { columns } from './table-columns';
	import FormDialog from './form-dialog.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>Scrapers</title>
</svelte:head>

<main class="mx-auto flex max-w-screen-md flex-col gap-2 p-4 pt-8">
	<h1 class="text-3xl font-bold">Scrapers</h1>
	<p class="text-sm text-muted-foreground">Manage servers running the Scraper API.</p>
	<DataTable data={data.servers} {columns} />
	<div class="mt-4 flex w-full flex-col items-center"><FormDialog {data} /></div>
</main>
