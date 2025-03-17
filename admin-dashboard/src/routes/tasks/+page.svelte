<!-- fyi: This script block needs to be here to make TS syntax work for #snippet, even if we don't import anything -->
<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { renderComponent } from '$lib/components/ui/data-table/render-helpers.js';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import type { ColumnDef } from '@tanstack/table-core';
	import SubtaskInfo from './subtask-info.svelte';
	import ButtonWithTextProp from '$lib/components/ui/button-with-text-prop.svelte';

	let { data } = $props();

	const tableColumns: ColumnDef<(typeof data.tasks)[number]>[] = [
		{
			accessorFn: (row) => row.task.id,
			header: 'ID'
		},
		{
			accessorFn: (row) => row.task.dataSource,
			header: 'Data Source'
		},
		{
			accessorFn: (row) => row.task.taskType,
			header: 'Task Type'
		},
		{
			accessorFn: (row) => row.task.params,
			header: 'Parameters'
		},
		{
			accessorFn: (row) => row.subTasksWithProgress,
			header: 'Subtasks',
			cell: ({ row }) =>
				renderComponent(SubtaskInfo, { subtasksWithProgress: row.original.subTasksWithProgress })
		},
		{
			accessorKey: 'details',
			header: '',
			cell: ({ row }) =>
				renderComponent(ButtonWithTextProp, {
					href: `/tasks/${row.original.task.id}`,
					variant: 'outline',
					text: 'Details'
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
	<DataTable data={data.tasks} columns={tableColumns} />
{/if}
