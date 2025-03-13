<script lang="ts">
	import { getDuckDB } from '$lib/duckdb.svelte';
	import { duckDBTableDescribeColumnsSchema, type FileSchemaPreviewColumns } from '.';
	import InputFileColumnsPreview from './input-file-schema-preview.svelte';
	import { FileInput } from '$lib/components/ui/file-input';
	import { Label } from '$lib/components/ui/label';
	import * as Alert from '$lib/components/ui/alert';
	import CircleAlert from 'lucide-svelte/icons/circle-alert';
	import ImportQueryEditor from './import-query-editor.svelte';

	let duckDB = getDuckDB();
	let detectedColumns: FileSchemaPreviewColumns[] | null = $state(null);

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
			const extractedColumnsDuckDB = duckDBTableDescribeColumnsSchema.parse(result.data);
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
</script>

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
	<h2 class="text-lg font-semibold">Detected columns</h2>
	<InputFileColumnsPreview data={detectedColumns} />
	<h2 class="text-lg font-semibold">Import query</h2>
	<span class="text-sm"
		>Enter a DuckDB SQL query (<code>SELECT ...</code>) to import the data from the file. It should
		produce results of type <code>string</code>.</span
	>
	{#if duckDB.value.state === 'ready'}
		<Alert.Root>
			<CircleAlert class="size-4" />
			<Alert.Title>Hint</Alert.Title>
			<Alert.Description>Use the detected schema/columns for reference.</Alert.Description>
		</Alert.Root>
		<ImportQueryEditor duckDB={duckDB.value.db} />
	{:else}
		<Alert.Root variant="destructive">
			<CircleAlert class="size-4" />
			<Alert.Title>Error</Alert.Title>
			<Alert.Description>Cannot process your file yet. Please try again later.</Alert.Description>
		</Alert.Root>
	{/if}
{/if}
