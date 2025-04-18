<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import type { ColumnDef } from '@tanstack/table-core';
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { buttonVariants } from '$lib/components/ui/button/index.js';
	import { renderComponent } from '$lib/components/ui/data-table';
	import type { SubtaskWithScraperAndProgress } from '$lib/server/scraper-api/tasks/get-progress';
	import AsyncValueCell from '$lib/components/ui/async-value-cell.svelte';

	const columns: ColumnDef<SubtaskWithScraperAndProgress>[] = [
		{ accessorFn: (row) => row.scraper.host, header: 'Host' },
		{ accessorFn: (row) => row.scraper.port, header: 'Port' },
		{
			header: 'Successes',
			cell: ({ row }) =>
				renderComponent(AsyncValueCell<typeof row.original.progress>, {
					valuePromise: row.original.progress,
					accessorFn: (progress) =>
						progress.status === 'success' ? progress.data.success_count : 'N/A'
				})
		},
		{
			header: 'Remaining',
			cell: ({ row }) =>
				renderComponent(AsyncValueCell<typeof row.original.progress>, {
					valuePromise: row.original.progress,
					accessorFn: (progress) =>
						progress.status === 'success' ? progress.data.remaining_count : 'N/A'
				})
		},
		{
			header: 'Failures',
			cell: ({ row }) =>
				renderComponent(AsyncValueCell<typeof row.original.progress>, {
					valuePromise: row.original.progress,
					accessorFn: (progress) =>
						progress.status === 'success' ? progress.data.failure_count : 'N/A'
				})
		},
		{
			header: 'Empty responses',
			cell: ({ row }) =>
				renderComponent(AsyncValueCell<typeof row.original.progress>, {
					valuePromise: row.original.progress,
					accessorFn: (progress) =>
						progress.status === 'success' ? progress.data.inputs_without_output_count : 'N/A'
				})
		}
	];

	let {
		subtasksWithProgress,
		wrapInDialog = true
	}: {
		subtasksWithProgress: SubtaskWithScraperAndProgress[];
		wrapInDialog?: boolean;
	} = $props();
</script>

{#if wrapInDialog}
	{#if subtasksWithProgress.length > 0}
		<Dialog.Root>
			<Dialog.Trigger class={buttonVariants({ variant: 'outline' })}>
				{subtasksWithProgress.length} subtask{subtasksWithProgress.length == 1 ? '' : 's'}
			</Dialog.Trigger>
			<Dialog.Content class="max-w-screen-md">
				<Dialog.Title>Subtask Status</Dialog.Title>
				<Dialog.Description>
					Each subtask is run as an individual task on separate scrapers. You can view the progress
					of each one here.
				</Dialog.Description>
				<DataTable {columns} data={subtasksWithProgress} />
			</Dialog.Content>
		</Dialog.Root>
	{:else}
		No subtasks
	{/if}
{:else if subtasksWithProgress.length > 0}
	<DataTable {columns} data={subtasksWithProgress} />
{:else}
	<span class="text-sm text-muted-foreground">No subtasks</span>
{/if}
