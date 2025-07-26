<script lang="ts">
	import DataTable from '$lib/components/ui/data-table.svelte';
	import type { ColumnDef, RowSelectionState } from '@tanstack/table-core';
	import { getTaskFormState } from './index.svelte';
	import type { Scraper } from '$lib/server/db/schema';
	import { renderComponent } from '$lib/components/ui/data-table';
	import { Checkbox } from '$lib/components/ui/checkbox';

	const state = getTaskFormState();
	let availableScrapers = $derived(state.availableScrapers);

	const columns: ColumnDef<Scraper>[] = [
		{
			id: 'select',
			header: ({ table }) =>
				renderComponent(Checkbox, {
					checked: table.getIsAllPageRowsSelected(),
					indeterminate: table.getIsSomePageRowsSelected() && !table.getIsAllPageRowsSelected(),
					onCheckedChange: (value) => table.toggleAllPageRowsSelected(!!value),
					'aria-label': 'Select all'
				}),
			cell: ({ row }) =>
				renderComponent(Checkbox, {
					checked: row.getIsSelected(),
					onCheckedChange: (value) => row.toggleSelected(!!value),
					'aria-label': 'Select row'
				}),
			enableSorting: false,
			enableHiding: false
		},
		{
			accessorKey: 'host',
			header: 'Host'
		},
		{
			accessorKey: 'port',
			header: 'Port'
		}
	];

	const handleSelectionChange = (newValue: RowSelectionState) => {
		const selectedScraperIdxs = Object.keys(newValue)
			.filter((key) => newValue[key]) // include only keys with a true value
			.map((key) => parseInt(key, 10)); // parse the keys as numbers
		const selectedIds = selectedScraperIdxs.map((idx) => availableScrapers[idx].id);
		state.selectedScraperIds = selectedIds;
	};
</script>

<DataTable
	{columns}
	data={availableScrapers}
	initialSelection={state.selectedScraperIds.reduce((acc, id) => {
		const idx = availableScrapers.findIndex((scraper) => scraper.id === id);
		if (idx !== -1) acc[idx] = true;
		return acc;
	}, {} as RowSelectionState)}
	onSelectionChange={handleSelectionChange}
	rowDescSingular="scraper"
	rowDescPlural="scrapers"
/>
