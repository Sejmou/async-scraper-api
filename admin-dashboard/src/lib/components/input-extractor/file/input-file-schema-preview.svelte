<script lang="ts">
	import { type ColumnDef, getCoreRowModel } from '@tanstack/table-core';
	import * as Table from '$lib/components/ui/table';
	import { createSvelteTable, FlexRender } from '$lib/components/ui/data-table';
	import { type FileSchemaPreviewColumns } from '.';

	let {
		data
	}: {
		data: FileSchemaPreviewColumns[];
	} = $props();

	const columnDefs: ColumnDef<FileSchemaPreviewColumns, string>[] = [
		{
			accessorKey: 'name',
			header: 'Column Name'
		},
		{
			accessorKey: 'type',
			header: 'Data Type'
		}
	];

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns: columnDefs,
		getCoreRowModel: getCoreRowModel()
	});
</script>

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
