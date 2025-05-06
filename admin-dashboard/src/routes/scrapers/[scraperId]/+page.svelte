<script lang="ts">
	import { goto, invalidate } from '$app/navigation';
	import DataTableExternalPagination from '$lib/components/ui/data-table-external-pagination.svelte';
	import { renderComponent } from '$lib/components/ui/data-table/render-helpers';
	import type { ColumnDef, OnChangeFn, PaginationState } from '@tanstack/table-core';
	import TaskStatus from '$lib/components/task-state-management/task-status.svelte';
	import TaskActions from './task-actions.svelte';
	import TaskFileUploads from './task-file-uploads.svelte';
	import { pauseTask, resumeTask } from '$lib/client-api/scrapers/tasks/state-management';
	import { timeAgo } from '$lib/utils';
	import ScraperTaskProgressTracker from '$lib/components/task-state-management/scraper-task-progress-tracker.svelte';

	let { data } = $props();
	let scraper = $derived(data.scraper);
	let status = $derived(data.status);
	let tasks = $derived(data.tasks.items);
	let pagination = $derived<PaginationState>({
		pageIndex: data.tasks.page - 1,
		pageSize: data.tasks.size
	});
	let rowCount = $derived(data.tasks.total);

	const handlePaginationChange: OnChangeFn<PaginationState> = (updater) => {
		const newState = typeof updater === 'function' ? updater(pagination) : updater;
		goto(`?page=${newState.pageIndex + 1}`);
	};

	type ScraperTask = (typeof data.tasks.items)[0];

	const taskTableColumns: ColumnDef<ScraperTask>[] = [
		{
			accessorKey: 'id',
			header: 'ID'
		},
		{
			accessorKey: 'data_source',
			header: 'Data Source'
		},
		{
			accessorKey: 'task_type',
			header: 'Task Type'
		},
		{
			accessorKey: 'params',
			header: 'Parameters',
			cell: ({ row }) => {
				return row.original.params ? JSON.stringify(row.original.params, null, 2) : 'None';
			}
		},
		{
			accessorKey: 'status',
			header: 'Status',
			cell: ({ row }) =>
				renderComponent(TaskStatus, {
					status: row.original.status,
					onPause: () => {
						pauseTask(scraper.id, row.original.id).then(() =>
							invalidate(`/scrapers/${scraper.id}`)
						);
					},
					onResume: () => {
						resumeTask(scraper.id, row.original.id).then(() =>
							invalidate(`/scrapers/${scraper.id}`)
						);
					}
				})
		},
		{
			header: 'Progress',
			cell: ({ row }) =>
				renderComponent(ScraperTaskProgressTracker, {
					scraperId: scraper.id,
					scraperTaskId: row.original.id
				})
		},
		{
			header: 'Created',
			accessorFn: (row) => timeAgo(row.created_at)
		},
		{
			header: 'Last Update',
			accessorFn: (row) => timeAgo(row.updated_at)
		},
		{
			accessorKey: 'file_uploads',
			header: 'Uploads',
			cell: ({ row }) =>
				renderComponent(TaskFileUploads, {
					fileUploads: row.original.file_uploads,
					taskId: row.original.id
				})
		},
		{
			accessorKey: 'actions',
			header: '',
			cell: ({ row }) =>
				renderComponent(TaskActions, {
					scraperId: scraper.id,
					taskId: row.original.id
				})
		}
	];
</script>

<svelte:head>
	<title>Scraper @ {scraper.protocol}://{scraper.host}:{scraper.port}</title>
</svelte:head>

<h2 class="text-2xl font-semibold">
	Scraper {scraper.id} ({scraper.protocol}://{scraper.host}:{scraper.port})
</h2>
<div class="flex items-center space-x-2">
	<div
		class="h-3 w-3 rounded-full"
		class:!bg-green-500={status === 'online'}
		class:!bg-red-500={status === 'offline'}
	></div>
	<span>{status === 'online' ? 'Online' : 'Offline'}</span>
</div>
<p class="text-sm text-muted-foreground">Added: {scraper.addedAt}</p>
<p class="text-sm text-muted-foreground">API Version: {data.version}</p>

<h3 class="mt-4 text-lg font-semibold">Tasks</h3>
{#if status === 'offline'}
	<p class="text-sm text-muted-foreground">Tasks could not be fetched as the scraper is offline.</p>
{:else if tasks.length === 0}
	<p class="text-sm text-muted-foreground">No tasks have been scheduled yet.</p>
{:else}
	<DataTableExternalPagination
		data={tasks}
		{pagination}
		{rowCount}
		columns={taskTableColumns}
		onPaginationChange={handlePaginationChange}
	/>
{/if}
