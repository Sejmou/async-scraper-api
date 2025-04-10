<script lang="ts" generics="TData, TValue">
	import {
		type ColumnDef,
		getCoreRowModel,
		getPaginationRowModel,
		type PaginationState,
		type RowSelectionState,
		type VisibilityState
	} from '@tanstack/table-core';
	import { createSvelteTable, FlexRender } from '$lib/components/ui/data-table';
	import * as Table from '$lib/components/ui/table';
	import * as Pagination from '$lib/components/ui/pagination';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { Button } from '$lib/components/ui/button';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';

	type DataTableProps<TData, TValue> = {
		columns: ColumnDef<TData, TValue>[];
		data: TData[];
		paginationPageSize?: number;
		rowDescSingular?: string;
		rowDescPlural?: string;
		showSelectedRowCount?: boolean;
		showColumnFilter?: boolean;
		onSelectionChange?: (newValue: RowSelectionState) => void;
	};

	let {
		data,
		columns,
		// by specifying default values, our typechecker knows that the optional props cannot be undefined <3
		onSelectionChange = () => {},
		paginationPageSize = 10,
		rowDescSingular = 'row',
		rowDescPlural = 'rows',
		showSelectedRowCount = false,
		showColumnFilter = false
	}: DataTableProps<TData, TValue> = $props();
	if (paginationPageSize < 1) {
		throw new Error('paginationPageSize must be greater than 0');
	}

	let pagination = $state<PaginationState>({
		pageIndex: 0,
		pageSize: paginationPageSize
	});

	let rowSelection = $state<RowSelectionState>({});

	let columnVisibility = $state<VisibilityState>({});
	$inspect(columnVisibility);

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		state: {
			get pagination() {
				return pagination;
			},
			get rowSelection() {
				return rowSelection;
			},
			get columnVisibility() {
				return columnVisibility;
			}
		},
		onPaginationChange: (updater) => {
			if (typeof updater === 'function') {
				pagination = updater(pagination);
			} else {
				pagination = updater;
			}
		},
		onRowSelectionChange: (updater) => {
			if (typeof updater === 'function') {
				rowSelection = updater(rowSelection);
			} else {
				rowSelection = updater;
			}
			onSelectionChange?.(rowSelection);
		},
		onColumnVisibilityChange: (updater) => {
			if (typeof updater === 'function') {
				columnVisibility = updater(columnVisibility);
			} else {
				columnVisibility = updater;
			}
		},

		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel()
	});

	function getPage() {
		return table.getState().pagination.pageIndex + 1;
	}

	function setPage(newPage: number) {
		table.setPageIndex(newPage - 1);
	}

	let pageIndex = $derived(table.getState().pagination.pageIndex);
	let pageCount = $derived(table.getPageCount());
	let rowCount = $derived(table.getCoreRowModel().rows.length);
	let rowCountAndDesc = $derived(
		`${rowCount} ` + (rowCount === 1 ? rowDescSingular : rowDescPlural)
	);
</script>

<div class="w-full">
	<div class="flex items-end pb-4">
		<div class="text-sm text-muted-foreground">
			{#if pageCount > 1}
				{rowCountAndDesc} (showing {rowDescPlural}
				{pageIndex * paginationPageSize + 1} to {Math.min(
					(pageIndex + 1) * paginationPageSize,
					rowCount
				)})
			{:else}
				{rowCountAndDesc}
			{/if}
		</div>
		{#if showColumnFilter}
			<DropdownMenu.Root>
				<DropdownMenu.Trigger>
					{#snippet child({ props })}
						<Button {...props} variant="outline" class="ml-auto">
							Columns <ChevronDown class="ml-2 size-4" />
						</Button>
					{/snippet}
				</DropdownMenu.Trigger>
				<DropdownMenu.Content align="end">
					{#each table.getAllColumns().filter((col) => col.getCanHide()) as column (column.id)}
						<DropdownMenu.CheckboxItem
							class="capitalize"
							bind:checked={() => column.getIsVisible(), (v) => column.toggleVisibility(!!v)}
						>
							{column.id}
						</DropdownMenu.CheckboxItem>
					{/each}
				</DropdownMenu.Content>
			</DropdownMenu.Root>
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
					<Table.Row data-state={row.getIsSelected() && 'selected'}>
						{#each row.getVisibleCells() as cell (cell.id)}
							<Table.Cell>
								<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
							</Table.Cell>
						{/each}
					</Table.Row>
				{:else}
					<Table.Row>
						<Table.Cell colspan={columns.length} class="h-24 text-center">No results.</Table.Cell>
					</Table.Row>
				{/each}
			</Table.Body>
		</Table.Root>
	</div>
	{#if showSelectedRowCount}
		<div class="flex-1 text-sm text-muted-foreground">
			{table.getFilteredSelectedRowModel().rows.length} of{' '}
			{table.getFilteredRowModel().rows.length} row(s) selected.
		</div>
	{/if}
	{#if pageCount > 1}
		<div class="mt-2 w-full">
			<Pagination.Root bind:page={getPage, setPage} count={rowCount} perPage={paginationPageSize}>
				{#snippet children({ pages, currentPage })}
					<Pagination.Content>
						<Pagination.Item>
							<Pagination.PrevButton disabled={!table.getCanPreviousPage()} />
						</Pagination.Item>
						{#each pages as page (page.key)}
							{#if page.type === 'ellipsis'}
								<Pagination.Item>
									<Pagination.Ellipsis />
								</Pagination.Item>
							{:else}
								<!-- TODO: make work -> isVisible={currentPage === page.value} -->
								<Pagination.Item>
									<Pagination.Link {page} isActive={currentPage === page.value}>
										{page.value}
									</Pagination.Link>
								</Pagination.Item>
							{/if}
						{/each}
						<Pagination.Item>
							<Pagination.NextButton disabled={!table.getCanNextPage()} />
						</Pagination.Item>
					</Pagination.Content>
				{/snippet}
			</Pagination.Root>
		</div>
	{/if}
</div>
