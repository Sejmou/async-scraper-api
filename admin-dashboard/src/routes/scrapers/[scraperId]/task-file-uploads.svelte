<script lang="ts">
	import { buttonVariants } from '$lib/components/ui/button';
	import DataTable from '$lib/components/ui/data-table.svelte';
	import * as Dialog from '$lib/components/ui/dialog';
	import { humanReadableSize } from '$lib/utils';
	import type { ColumnDef } from '@tanstack/table-core';

	let {
		fileUploads,
		taskId
	}: {
		fileUploads: {
			id: number;
			task_id: number;
			s3_key: string;
			s3_bucket: string;
			s3_endpoint_url: string;
			size_bytes: number;
			uploaded_at: string;
		}[];
		taskId: number;
	} = $props();

	const columns: ColumnDef<(typeof fileUploads)[number]>[] = [
		{
			accessorKey: 's3_key',
			header: 'S3 Key'
		},
		{
			accessorKey: 's3_bucket',
			header: 'S3 Bucket'
		},
		{
			accessorKey: 's3_endpoint_url',
			header: 'S3 Endpoint URL'
		},
		{
			accessorKey: 'size_bytes',
			header: 'Size',
			cell: ({ row }) => humanReadableSize(row.original.size_bytes)
		},
		{
			accessorKey: 'uploaded_at',
			header: 'Uploaded At'
		}
	];
</script>

{#if fileUploads.length === 0}
	<p class="text-sm text-muted-foreground">None yet.</p>
{:else}
	<Dialog.Root>
		<Dialog.Trigger class={buttonVariants({ variant: 'outline' })}>
			{fileUploads.length} file{fileUploads.length == 1 ? '' : 's'} ({humanReadableSize(
				fileUploads.reduce((acc, file) => acc + file.size_bytes, 0)
			)})
		</Dialog.Trigger>
		<Dialog.Content class="max-w-screen-lg">
			<Dialog.Header>
				<Dialog.Title>Uploads for Task ID {taskId}</Dialog.Title>
				<Dialog.Description>
					<DataTable data={fileUploads} {columns} />
				</Dialog.Description>
			</Dialog.Header>
		</Dialog.Content>
	</Dialog.Root>
{/if}
