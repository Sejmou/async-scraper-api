<script lang="ts">
	import { goto } from '$app/navigation';
	import DataTableExternalPagination from '$lib/components/ui/data-table-external-pagination.svelte';
	import type { ColumnDef, OnChangeFn, PaginationState } from '@tanstack/table-core';
	import { online } from 'svelte/reactivity/window';

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
			accessorKey: 'status',
			header: 'Status'
		},
		{
			accessorKey: 'created_at',
			header: 'Created At'
		},
		{
			accessorKey: 'updated_at',
			header: 'Updated At'
		}
	];
</script>

<h2 class="text-2xl font-semibold">
	Scraper at {scraper.protocol}://{scraper.host}:{scraper.port}
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
