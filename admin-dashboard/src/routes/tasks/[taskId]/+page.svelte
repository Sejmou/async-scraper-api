<script lang="ts">
	import type { ColumnDef } from '@tanstack/table-core';
	import { renderComponent } from '$lib/components/ui/data-table';
	import ScraperTaskProgressTracker from '$lib/components/task-state-management/scraper-task-progress-tracker.svelte';
	import ScraperTaskManager from '$lib/components/task-state-management/scraper-task-manager.svelte';
	import DataTable from '$lib/components/ui/data-table.svelte';

	let { data } = $props();
	let task = $derived(data.task);
	$inspect(data);

	type Subtask = (typeof task)['subtasks'][number];

	let columns: ColumnDef<Subtask>[] = $derived([
		{ accessorFn: (row) => row.scraper.host, header: 'Host' },
		{ accessorFn: (row) => row.scraper.port, header: 'Port' },
		{
			header: 'Status',
			cell: ({ row }) =>
				renderComponent(ScraperTaskManager, {
					scraperId: row.original.scraperId,
					scraperTaskId: row.original.scraperTaskId
				})
		},
		{
			header: 'Progress',
			cell: ({ row }) =>
				renderComponent(ScraperTaskProgressTracker, {
					scraperId: row.original.scraperId,
					scraperTaskId: row.original.scraperTaskId
				})
		}
	]);
</script>

<DataTable {columns} data={task.subtasks} />
