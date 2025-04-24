<script lang="ts">
	import GroupedStackedBarChartVertical from '$lib/components/charts/grouped-stacked-bar-chart-vertical.svelte';
	import StackedBarChartHorizontal from '$lib/components/charts/stacked-bar-chart-horizontal.svelte';
</script>

<div class="flex w-full flex-col border">
	<h3 class="text-xl font-bold">Grouped Stacked Bar Chart (Vertical Bars)</h3>
	<GroupedStackedBarChartVertical
		variables={['Processed', 'Errors', 'Remaining']}
		categoryDescription="Scraper"
		categories={['Scraper 1', 'Scraper 2', 'Scraper 3']}
		data={[
			{
				quantitativeVariables: { Processed: 100, Errors: 10, Remaining: 90 },
				category: 'Scraper 1'
			},
			{
				quantitativeVariables: { Processed: 200, Errors: 20, Remaining: 180 },
				category: 'Scraper 2'
			},
			{
				quantitativeVariables: { Processed: 300, Errors: 30, Remaining: 270 },
				category: 'Scraper 3'
			}
		]}
	/>

	<StackedBarChartHorizontal
		data={[
			{
				label: 'Done',
				value: 100,
				color: '#4caf50'
			},
			{
				label: 'Error',
				value: 20,
				color: '#f44336'
			},
			{
				label: 'No Data',
				value: 30,
				color: '#fbc02d'
			},
			{
				label: 'Pending',
				value: 50,
				color: '#ccc'
			}
		]}
		dataDescSingular="input"
		dataDescPlural="inputs"
	/>
</div>
