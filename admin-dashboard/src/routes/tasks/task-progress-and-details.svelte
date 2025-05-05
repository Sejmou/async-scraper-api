<script lang="ts">
	import type { ColumnDef } from '@tanstack/table-core';
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { renderComponent } from '$lib/components/ui/data-table';
	import type { Scraper, Subtask } from '$lib/server/db/schema';
	import ScraperTaskProgress from '$lib/components/scraper-task-progress.svelte';
	import {
		fetchTaskProgress,
		type TaskProgressFetchPromise
	} from '$lib/client-server-communication/scraper-api/tasks/progress';
	import type { TaskProgress } from '$lib/types-and-schemas/tasks/common';
	import * as Dialog from '$lib/components/ui/dialog';
	import { buttonVariants } from '$lib/components/ui/button';
	import { browser } from '$app/environment';

	type SubtaskWithScraper = Subtask & { scraper: Scraper };

	let {
		taskId,
		dataSource,
		taskType,
		createdAt,
		subtasks
	}: {
		taskId: number;
		dataSource: string;
		taskType: string;
		createdAt: string;
		subtasks: SubtaskWithScraper[];
	} = $props();

	let subtasksAndProgressPromises: {
		subtask: SubtaskWithScraper;
		progressPromise: TaskProgressFetchPromise;
	}[] = $derived.by(() => {
		if (!browser) {
			return subtasks.map((subtask) => ({
				subtask,
				progressPromise: Promise.resolve({
					status: 'success',
					data: {
						success_count: 0,
						failure_count: 0,
						inputs_without_output_count: 0,
						remaining_count: 0
					}
				})
			}));
		}
		return subtasks.map((subtask) => ({
			subtask,
			progressPromise: fetchTaskProgress(subtask.scraperId, subtask.taskId)
		}));
	});

	let columns: ColumnDef<SubtaskWithScraper>[] = $derived([
		{ accessorFn: (row) => row.scraper.host, header: 'Host' },
		{ accessorFn: (row) => row.scraper.port, header: 'Port' },
		{
			header: 'Status',
			accessorFn: (row) => 'asdf'
		},
		{
			header: 'Progress',
			cell: ({ row }) =>
				renderComponent(ScraperTaskProgress, {
					promise: subtasksAndProgressPromises.find(
						(el) =>
							el.subtask.scraperId === row.original.scraperId &&
							el.subtask.scraperTaskId === row.original.scraperTaskId
					)!.progressPromise
				})
		}
	]);

	let overallProgressPromise: TaskProgressFetchPromise = $derived(
		Promise.all(subtasksAndProgressPromises.map((el) => el.progressPromise)).then((results) => {
			let cumulative: TaskProgress = {
				success_count: 0,
				failure_count: 0,
				inputs_without_output_count: 0,
				remaining_count: 0
			};

			for (const item of results) {
				if (item.status === 'error') {
					// Reject the promise by throwing
					throw new Error('One or more items have status "error".');
				}
				cumulative.success_count += item.data.success_count;
				cumulative.failure_count += item.data.failure_count;
				cumulative.remaining_count += item.data.remaining_count;
				cumulative.inputs_without_output_count += item.data.inputs_without_output_count;
			}

			return {
				status: 'success',
				data: cumulative
			};
		})
	);

	let scraperDesc = $derived(subtasks.length > 1 ? `${subtasks.length} scrapers` : '1 scraper');
</script>

{#if subtasks.length > 0}
	<div class="flex gap-2">
		<ScraperTaskProgress
			promise={overallProgressPromise}
			dataDescSingular={`item (${scraperDesc})`}
			dataDescPlural={`items (${scraperDesc})`}
		/>
		<Dialog.Root>
			<Dialog.Trigger class={buttonVariants({ variant: 'outline' })}>Details</Dialog.Trigger>
			<Dialog.Content class="max-w-screen-md">
				<Dialog.Header>
					<Dialog.Title>
						Task {taskId} (<code>{dataSource}/{taskType}</code>, {scraperDesc})
					</Dialog.Title>
					<Dialog.Description>created at: {createdAt}</Dialog.Description>
				</Dialog.Header>
				<DataTable {columns} data={subtasks} />
			</Dialog.Content>
		</Dialog.Root>
	</div>
{:else}
	<span class="text-sm text-muted-foreground">No subtasks</span>
{/if}
