<script lang="ts">
	import FileInput from '../ui/file-input/file-input.svelte';
	import { Label } from '../ui/label';
	import * as Dialog from '../ui/dialog';
	import { buttonVariants } from '../ui/button';
	import { getDuckDB } from '$lib/duckdb.svelte';
	import { extractedColumnsSchema, type FileColumnPreviewColumns } from '.';
	import InputFileColumnsPreview from './input-file-columns-preview.svelte';
	import type { JSONSerializableValue } from '$lib/utils';

	let duckDB = getDuckDB();
	let detectedColumns: FileColumnPreviewColumns[] | null = $state(null);

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
		await db.createTableFromFile(file, 'inputs');
		const result = await db.executeQueryRowMajor('DESCRIBE inputs');
		if (result.type === 'result') {
			const extractedColumnsDuckDB = extractedColumnsSchema.parse(result.data);
			if (extractedColumnsDuckDB.length === 0) {
				alert('No columns detected in the file. Please try again.');
				return;
			} else if (extractedColumnsDuckDB.length == 1) {
				const { column_name, column_type } = extractedColumnsDuckDB[0];
				const inputColAlias = 'input_col';
				const inputColExpr =
					column_type !== 'VARCHAR' ? `CAST(${column_name}, VARCHAR)` : column_name;
				const inputsQueryRes = await db.executeQueryColumnMajor(
					`SELECT ${inputColExpr} AS ${inputColAlias} FROM inputs`
				);
				if (inputsQueryRes.type === 'error') {
					alert('Error extracting data from the file. Please try again.');
					return;
				}
				const inputs = inputsQueryRes.data[inputColAlias];
				console.log(inputs);
			}
			detectedColumns = extractedColumnsDuckDB.map((row) => ({
				name: row.column_name,
				type: row.column_type
			}));
		}
		console.log(result);
	};

	let {
		value = $bindable([]),
		inputDescription
	}: { value: JSONSerializableValue[]; inputDescription: string } = $props();
</script>

<div class="grid w-full max-w-sm items-center gap-1.5">
	<Label for="ids-file">{inputDescription}</Label>
	<Dialog.Root>
		<Dialog.Trigger class={buttonVariants({ variant: 'outline' })}>Add</Dialog.Trigger>
		<Dialog.Content class="max-w-screen-md">
			<Dialog.Header>
				<Dialog.Title>Add {inputDescription}</Dialog.Title>
				<Dialog.Description>
					You can extract them from a file (<code>.txt</code>, <code>.csv</code>, or
					<code>.parquet</code>) or by copy-pasting them into a text area.
				</Dialog.Description>
			</Dialog.Header>
			<h2 class="text-xl font-semibold">File with input data</h2>
			<div class="grid w-full max-w-sm items-center gap-1.5">
				<Label for="ids-file">Select a file</Label>
				<FileInput
					disabled={duckDB.value.state !== 'ready'}
					oninput={handleFileInput}
					id="ids-file"
					type="file"
				/>
			</div>
			{#if detectedColumns !== null}
				<h2 class="text-xl font-semibold">Relevant columns</h2>
				<InputFileColumnsPreview data={detectedColumns} />
			{/if}
		</Dialog.Content>
	</Dialog.Root>
</div>
