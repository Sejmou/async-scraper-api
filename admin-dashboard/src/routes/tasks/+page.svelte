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
			accessorKey: 'id',
			header: 'ID'
		},
		{
			accessorKey: 'dataSource',
			header: 'Data Source'
		},
		{
			accessorKey: 'taskType',
			header: 'Task Type'
		},
		{
			accessorKey: 'params',
			header: 'Parameters'
		},
		{
			accessorKey: 'subtasks',
			header: 'Subtasks',
			cell: ({ row }) => renderComponent(SubtaskInfo, { subtasks: row.original.subtasks })
		},
		{
			accessorKey: 'details',
			header: '',
			cell: ({ row }) =>
				renderComponent(ButtonWithTextProp, {
					href: `/tasks/${row.original.id}`,
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
