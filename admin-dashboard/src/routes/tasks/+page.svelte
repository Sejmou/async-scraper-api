<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { renderComponent } from '$lib/components/ui/data-table/render-helpers.js';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import type { ColumnDef } from '@tanstack/table-core';
	import TaskProgressAndDetails from './task-progress-and-details.svelte';

	let { data } = $props();

	const tableColumns: ColumnDef<(typeof data.tasks)[number]>[] = [
		{
			accessorFn: (row) => row.id,
			header: 'ID'
		},
		{
			accessorFn: (row) => row.dataSource,
			header: 'Data Source'
		},
		{
			accessorFn: (row) => row.taskType,
			header: 'Task Type'
		},
		{
			accessorFn: (row) => (row.params ? JSON.stringify(row.params) : 'No parameters'),
			header: 'Parameters'
		},
		{
			header: 'Progress',
			cell: ({ row }) =>
				renderComponent(TaskProgressAndDetails, {
					taskId: row.original.id,
					taskType: row.original.taskType,
					dataSource: row.original.dataSource,
					createdAt: row.original.createdAt,
					subtasks: row.original.subtasks
				})
		}
	];
</script>

<svelte:head>
	<title>Tasks</title>
</svelte:head>

<PageHeading heading="Tasks" text="Create tasks for your scrapers and monitor their progress." />

{#if data.tasks.length === 0}
	<p class="text-sm text-muted-foreground">No tasks yet. Create one first!</p>
	<div>
		<Button href="/tasks/create">Create new task</Button>
	</div>
{:else}
	<div class="flex w-full justify-end">
		<Button href="/tasks/create">Create new task</Button>
	</div>
	<DataTable
		data={data.tasks}
		columns={tableColumns}
		rowDescPlural="tasks"
		rowDescSingular="task"
	/>
{/if}
