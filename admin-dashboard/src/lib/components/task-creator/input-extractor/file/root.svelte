<script lang="ts" generics="T extends z.ZodSchema">
	import { getDuckDB } from '$lib/duckdb.svelte';
	import { duckDBTableDescribeColumnsSchema, type FileSchemaPreviewColumns } from '.';
	import InputFileColumnsPreview from './input-file-schema-preview.svelte';
	import { FileInput } from '$lib/components/ui/file-input';
	import { Label } from '$lib/components/ui/label';
	import * as Alert from '$lib/components/ui/alert';
	import CircleAlert from 'lucide-svelte/icons/circle-alert';
	import ImportQueryEditor from './import-query-editor.svelte';
	import { z } from 'zod';
	import type { InputExtractorState } from '../index.svelte';

	let { ieState }: { ieState: InputExtractorState<T> } = $props();

	let duckDB = getDuckDB();
	let detectedColumns: FileSchemaPreviewColumns[] | null = $state(null);

	let file: File | null = $state(null);
	let files: FileList | undefined = $derived.by(() => {
		if (file) {
			// cannot directly programmatically set files on input
			// we need to use DataTransfer as 'mediator' in https://stackoverflow.com/a/68182158/13727176
			const dataTransfer = new DataTransfer();
			dataTransfer.items.add(file);
			return dataTransfer.files;
		} else {
			return;
		}
	});

	const handleFileInput = async (event: Event) => {
		if (duckDB.value.state !== 'ready') {
			alert('Cannot process your file yet. Please try again later.');
			return;
		}
		const db = duckDB.value.db;

		const target = event.target;
		if (!(target instanceof HTMLInputElement && target.files)) {
			console.error('No files in input event target! This is probably a programmer error.');
			return;
		}
		const files = target.files;
		if (!files) {
			console.error('No files in input event target! This is probably a programmer error.');
			return;
		}
		if (files.length > 1) {
			console.error('Only one file allowed');
			return;
		}
		// check file
		let file = files[0];
		console.log(file);
		if (!file) {
			console.error('No file selected!');
			return;
		}
		const tableName = 'inputs';
		await db.createTableFromFile(file, tableName);
		const result = await db.executeQueryRowMajor(`DESCRIBE ${tableName}`);
		if (result.type === 'result') {
			const extractedColumnsDuckDB = duckDBTableDescribeColumnsSchema.parse(result.data);
			if (extractedColumnsDuckDB.length === 0) {
				alert('No columns detected in the file. Please try again.');
				return;
			} else if (extractedColumnsDuckDB.length == 1) {
				const { column_name } = extractedColumnsDuckDB[0];
				const inputColAlias = 'input_col';
				const inputsQueryRes = await db.executeQueryColumnMajor(
					`SELECT ${column_name} FROM ${tableName}`
				);
				if (inputsQueryRes.type === 'error') {
					alert('Error extracting data from the file. Please try again.');
					return;
				}
				const inputs = inputsQueryRes.data[inputColAlias];
			}
			detectedColumns = extractedColumnsDuckDB.map((row) => ({
				name: row.column_name,
				type: row.column_type
			}));
		}
		console.log(result);
	};
</script>

<div class="grid w-full max-w-sm items-center gap-1.5">
	<Label for="ids-file">Select a file</Label>
	<FileInput
		disabled={duckDB.value.state !== 'ready'}
		oninput={handleFileInput}
		{files}
		id="ids-file"
		type="file"
	/>
</div>
{#if detectedColumns !== null}
	<h2 class="text-lg font-semibold">Detected columns</h2>
	<InputFileColumnsPreview data={detectedColumns} />
	<h2 class="text-lg font-semibold">Import query</h2>
	<p class="text-sm">
		Enter a DuckDB SQL query (<code>SELECT ...</code>) to import the data from the file. Each
		extracted input (i.e. row returned from the query) should match the schema of the following
		example:
	</p>
	<pre class="text-sm text-muted-foreground">{JSON.stringify(ieState.exampleInput, null, 2)}</pre>
	{#if duckDB.value.state === 'ready'}
		<Alert.Root>
			<CircleAlert class="size-4" />
			<Alert.Title>Hint</Alert.Title>
			<Alert.Description
				>Your file is available as a table called <code>inputs</code>. Use the inferred schema above
				for reference.</Alert.Description
			>
		</Alert.Root>
		<ImportQueryEditor {ieState} db={duckDB.value.db} />
	{:else}
		<Alert.Root variant="destructive">
			<CircleAlert class="size-4" />
			<Alert.Title>Error</Alert.Title>
			<Alert.Description>Cannot process your file yet. Please try again later.</Alert.Description>
		</Alert.Root>
	{/if}
{/if}
