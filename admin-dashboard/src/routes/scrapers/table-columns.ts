import type { ColumnDef } from '@tanstack/table-core';
import TableStatus from './table-status.svelte';
import { renderComponent } from '$lib/components/ui/data-table';

export type APIServerMeta = {
	host: string;
	version: string | null;
	online: boolean;
};

export const columns: ColumnDef<APIServerMeta>[] = [
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
	}
];
