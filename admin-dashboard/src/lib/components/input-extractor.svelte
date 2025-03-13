<script lang="ts">
	import FileInput from './ui/file-input/file-input.svelte';
	import { Label } from './ui/label';
	import * as Dialog from './ui/dialog';
	import { buttonVariants } from './ui/button';
	import { getDuckDB, type QueryResultRowMajor } from '$lib/duckdb.svelte';

	let duckDB = getDuckDB();
	let detectedColumns: QueryResultRowMajor['data'] | null = $state(null);

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
		const result = await db.executeQuery('DESCRIBE inputs');
		if (result.type === 'result') {
			detectedColumns = result.data;
		}
		console.log(result);
	};

	let { value = $bindable(), inputDescription }: { value: string[]; inputDescription: string } =
		$props();
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
				<pre>{JSON.stringify(detectedColumns, null, 2)}</pre>
			{/if}
		</Dialog.Content>
	</Dialog.Root>
</div>
