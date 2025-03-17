<script lang="ts" generics="TData, TValue">
	import {
		type ColumnDef,
		getCoreRowModel,
		getPaginationRowModel,
		type PaginationState
	} from '@tanstack/table-core';
	import { createSvelteTable, FlexRender } from '$lib/components/ui/data-table';
	import * as Table from '$lib/components/ui/table';
	import * as Pagination from '$lib/components/ui/pagination';

	type DataTableProps<TData, TValue> = {
		columns: ColumnDef<TData, TValue>[];
		data: TData[];
		paginationPageSize?: number;
		rowDescSingular?: string;
		rowDescPlural?: string;
	};

	let {
		data,
		columns,
		// by specifying default values, our typechecker knows that the optional props cannot be undefined <3
		paginationPageSize = 10,
		rowDescSingular = 'row',
		rowDescPlural = 'rows'
	}: DataTableProps<TData, TValue> = $props();
	if (paginationPageSize < 1) {
		throw new Error('paginationPageSize must be greater than 0');
	}

	let pagination = $state<PaginationState>({
		pageIndex: 0,
		pageSize: paginationPageSize
	});

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		state: {
			get pagination() {
				return pagination;
			}
		},
		onPaginationChange: (updater) => {
			if (typeof updater === 'function') {
				pagination = updater(pagination);
			} else {
				pagination = updater;
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
	<div class="w-full text-sm text-muted-foreground">
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
