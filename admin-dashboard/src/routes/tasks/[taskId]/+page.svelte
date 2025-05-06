<script lang="ts">
	import type { ColumnDef } from '@tanstack/table-core';
	import { renderComponent } from '$lib/components/ui/data-table';
	import ScraperTaskProgressTracker from '$lib/components/tasks/scraper-task-progress-tracker.svelte';
	import ScraperTaskManager from '$lib/components/tasks/scraper-task-manager.svelte';
	import DataTable from '$lib/components/ui/data-table.svelte';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import ButtonWithTextProp from '$lib/components/ui/button-with-text-prop.svelte';

	let { data } = $props();
	let task = $derived(data.task);

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
		},
		{
			id: 'actions',
			cell: ({ row }) => {
				return renderComponent(ButtonWithTextProp, {
					text: 'Details',
					href: `/scraper-tasks/${row.original.id}`,
					variant: 'outline'
				});
			}
		}
	]);
</script>

<PageHeading heading="Task {task.id}" text="" />
<ul class="list-disc pl-4">
	<li class="text-sm text-muted-foreground">
		Data Source: {task.dataSource}
	</li>
	<li class="text-sm text-muted-foreground">
		Task Type: {task.taskType}
	</li>
	<li class="text-sm text-muted-foreground">
		Created: {task.createdAt}
	</li>
</ul>

<h3 class="mt-4 text-xl font-semibold">Parameters</h3>
<pre class="text-sm">
{task.params ? JSON.stringify(task.params, null, 2) : 'No parameters'}
</pre>

<h3 class="mt-4 text-xl font-semibold">Subtasks</h3>

<DataTable {columns} data={task.subtasks} rowDescPlural={'subtasks'} rowDescSingular={'subtask'} />
