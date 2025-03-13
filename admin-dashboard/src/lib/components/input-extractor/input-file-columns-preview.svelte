<script lang="ts">
	import { type ColumnDef, type RowSelectionState, getCoreRowModel } from '@tanstack/table-core';
	import * as Table from '$lib/components/ui/table';
	import { createSvelteTable, FlexRender } from '$lib/components/ui/data-table';
	import { type FileColumnPreviewColumns } from '.';
	import * as Alert from '$lib/components/ui/alert';
	import CircleAlert from 'lucide-svelte/icons/circle-alert';

	let {
		data
	}: {
		data: FileColumnPreviewColumns[];
	} = $props();

	const columnDefs: ColumnDef<FileColumnPreviewColumns, string>[] = [
		{
			accessorKey: 'name',
			header: 'Column Name'
		},
		{
			accessorKey: 'type',
			header: 'Data Type'
		}
	];

	let rowSelection = $state<RowSelectionState>({});

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns: columnDefs,
		onRowSelectionChange: (updater) => {
			console.log(updater);
			if (typeof updater === 'function') {
				rowSelection = updater(rowSelection);
			} else {
				rowSelection = updater;
			}
		},
		state: {
			get rowSelection() {
				return rowSelection;
			}
		},
		getCoreRowModel: getCoreRowModel()
	});

	let selectedCols: string[] = $state([]);

	$inspect(rowSelection);

	$effect(() => {
		const selectedRowIdxs = Object.keys(rowSelection).map(Number);
		selectedCols = selectedRowIdxs.map((idx) => data[idx].name);
	});
</script>

<Alert.Root>
	<CircleAlert class="size-4" />
	<Alert.Title>File contains multiple columns</Alert.Title>
	<Alert.Description>
		Please select which column you want to extract the data from.
	</Alert.Description>
</Alert.Root>
<div class="flex-1">
	{#if selectedCols.length > 0}
		Selected columns: {selectedCols.join(', ')}
	{:else}
		No columns selected.
	{/if}
</div>
<div class="rounded-md border">
	<Table.Root>
		<Table.Header>
			{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
				<Table.Row>
					{#each headerGroup.headers as header (header.id)}
						<Table.Head>
							{#if !header.isPlaceholder}
								<FlexRender
									content={header.column.columnDef.header}
									context={header.getContext()}
								/>
							{/if}
						</Table.Head>
					{/each}
				</Table.Row>
			{/each}
		</Table.Header>
		<Table.Body>
			{#each table.getRowModel().rows as row (row.id)}
				<Table.Row
					onclick={() => row.toggleSelected()}
					data-state={row.getIsSelected() && 'selected'}
				>
					{#each row.getVisibleCells() as cell (cell.id)}
						<Table.Cell>
							<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
						</Table.Cell>
					{/each}
				</Table.Row>
			{:else}
				<Table.Row>
					<Table.Cell colspan={columnDefs.length} class="h-24 text-center">No results.</Table.Cell>
				</Table.Row>
			{/each}
		</Table.Body>
	</Table.Root>
</div>
