<script lang="ts">
	import {
		type SubTaskSelect as SubTask,
		type ScraperSelect as Scraper
	} from '$lib/server/db/schema';
	import * as Dialog from '$lib/components/ui/dialog';
	import type { ColumnDef } from '@tanstack/table-core';
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { buttonVariants } from '$lib/components/ui/button/index.js';

	const columns: ColumnDef<SubTaskWithScraper>[] = [
		{ accessorFn: (row) => row.scraper.host, header: 'Host' },
		{ accessorFn: (row) => row.scraper.port, header: 'Port' }
	];

	type SubTaskWithScraper = SubTask & { scraper: Scraper };

	let {
		subtasks,
		wrapInDialog = true
	}: {
		subtasks: SubTaskWithScraper[];
		wrapInDialog?: boolean;
	} = $props();
</script>

{#if wrapInDialog}
	{#if subtasks.length > 0}
		<Dialog.Root>
			<Dialog.Trigger class={buttonVariants({ variant: 'outline' })}>
				{subtasks.length} scraper{subtasks.length == 1 ? '' : 's'}
			</Dialog.Trigger>
			<Dialog.Content>
				<Dialog.Title>Subtasks</Dialog.Title>
				<Dialog.Description>
					<DataTable {columns} data={subtasks} />
				</Dialog.Description>
			</Dialog.Content>
		</Dialog.Root>
	{:else}
		No subtasks
	{/if}
{:else if subtasks.length > 0}
	<DataTable {columns} data={subtasks} />
{:else}
	<span class="text-sm text-muted-foreground">No subtasks</span>
{/if}
