import type { ColumnDef } from '@tanstack/table-core';

export type APIServerMeta = {
	ip_and_port: string;
	version: string | null;
	online: boolean;
};

export const columns: ColumnDef<APIServerMeta>[] = [
	{
		accessorKey: 'ip_and_port',
		header: 'IP Address and Port'
	},
	{
		accessorKey: 'version',
		header: 'API Version'
	},
	{
		accessorKey: 'online',
		header: 'Status'
	}
];
