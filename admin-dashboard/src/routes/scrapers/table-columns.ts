import type { ColumnDef } from '@tanstack/table-core';
import TableStatus from './table-status.svelte';
import TableActions from './table-actions.svelte';
import { renderComponent } from '$lib/components/ui/data-table';

export type ScraperMetadata = {
	id: number;
	host: string;
	version: string | null;
	online: boolean;
};

export const columns: ColumnDef<ScraperMetadata>[] = [
	{
		accessorKey: 'id',
		header: 'ID'
	},
	{
		accessorKey: 'host',
		header: 'Host'
	},
	{
		accessorKey: 'version',
		header: 'API Version'
	},
	{
		id: 'status',
		header: 'Status',
		cell: ({ row }) => {
			return renderComponent(TableStatus, { online: row.original.online });
		}
	},
	{
		id: 'actions',
		cell: ({ row }) => {
			return renderComponent(TableActions, { id: row.original.id, host: row.original.host });
		}
	}
];
