<script lang="ts">
	import BarChart from '$lib/components/charts/bar-chart.svelte';
</script>

<h3 class="text-xl font-bold">Grouped Stacked Bar Chart (Vertical Bars)</h3>
<BarChart
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
