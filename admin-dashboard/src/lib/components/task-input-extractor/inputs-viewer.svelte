<script lang="ts" generics="T extends z.ZodSchema">
	import * as Dialog from '$lib/components/ui/dialog';
	import { z } from 'zod';
	import type { InputExtractorState } from './index.svelte';
	import DataTableExternalPagination from '../ui/data-table-external-pagination.svelte';
	import type { OnChangeFn, PaginationState } from '@tanstack/table-core';

	let { ieState, open = $bindable() }: { ieState: InputExtractorState<T>; open: boolean } =
		$props();

	let pagination: PaginationState = $state({
		pageSize: 10,
		pageIndex: 0
	});

	let inputsSlice = $derived.by(() => {
		const { pageIndex, pageSize } = pagination;
		const startIdx = pageIndex * pageSize;
		const endIdx = startIdx + pageSize;
		return ieState.inputs.slice(startIdx, endIdx).map((input) => ({ data: input }));
	});
	$inspect(inputsSlice);

	const handlePaginationChange: OnChangeFn<PaginationState> = (updater) => {
		if (typeof updater === 'function') {
			pagination = updater(pagination);
		} else {
			pagination = updater;
		}
	};
</script>

<Dialog.Root bind:open>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>
				Imported {ieState.inputDescription}
			</Dialog.Title>
		</Dialog.Header>
		<DataTableExternalPagination
			data={inputsSlice}
			columns={[
				{
					header: 'Data',
					accessorKey: 'data'
				}
			]}
			{pagination}
			onPaginationChange={handlePaginationChange}
			rowCount={ieState.inputs.length}
		/>
	</Dialog.Content>
</Dialog.Root>
