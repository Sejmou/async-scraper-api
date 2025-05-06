<script lang="ts">
	import { type TaskProgress } from '$lib/types-and-schemas/tasks/common';
	import StackedBarChartHorizontal from '$lib/components/charts/stacked-bar-chart-horizontal.svelte';

	let {
		progress,
		dataDescSingular = 'item',
		dataDescPlural = 'items'
	}: {
		progress: TaskProgress;
		dataDescSingular?: string;
		dataDescPlural?: string;
	} = $props();
</script>

<StackedBarChartHorizontal
	data={[
		{
			label: 'Responses with data',
			value: progress.success_count,
			color: '#4caf50'
		},
		{
			label: 'Failed requests',
			value: progress.failure_count,
			color: '#f44336'
		},
		{
			label: 'Empty responses',
			value: progress.inputs_without_output_count,
			color: '#fbc02d'
		},
		{
			label: 'Left to fetch',
			value: progress.remaining_count,
			color: '#ccc'
		}
	]}
	{dataDescSingular}
	{dataDescPlural}
/>
