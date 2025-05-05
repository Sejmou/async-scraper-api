<script lang="ts">
	import { type TaskProgressFetchPromise } from '$lib/client-server-communication/scraper-api/tasks/progress';
	import StackedBarChartHorizontal from '$lib/components/charts/stacked-bar-chart-horizontal.svelte';

	let {
		promise,
		dataDescSingular = 'item',
		dataDescPlural = 'items'
	}: {
		promise: TaskProgressFetchPromise;
		dataDescSingular?: string;
		dataDescPlural?: string;
	} = $props();
</script>

{#await promise}
	<p>Loading...</p>
{:then progress}
	{#if progress.status === 'success'}
		{@const data = [
			{
				label: 'Responses with data',
				value: progress.data.success_count,
				color: '#4caf50'
			},
			{
				label: 'Failed requests',
				value: progress.data.failure_count,
				color: '#f44336'
			},
			{
				label: 'Empty responses',
				value: progress.data.inputs_without_output_count,
				color: '#fbc02d'
			},
			{
				label: 'Left to fetch',
				value: 50,
				color: '#ccc'
			}
		]}
		<StackedBarChartHorizontal {data} {dataDescSingular} {dataDescPlural} />
	{:else}
		<p>HTTP Error {progress.httpCode}: {progress.message}</p>
	{/if}
{:catch error}
	<p>Error: {error.message}</p>
{/await}
