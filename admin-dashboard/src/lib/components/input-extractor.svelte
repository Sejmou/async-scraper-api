<script lang="ts">
	import FileInput from './ui/file-input/file-input.svelte';
	import { Label } from './ui/label';
	import * as Dialog from './ui/dialog';
	import { buttonVariants } from './ui/button';

	const handleFileInput = async (event: Event) => {
		// const database = get(db);
		// if (!database) {
		// 	alert('The database is not initialized yet, cannot execute query!');
		// 	return;
		// }
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
		const file = files[0];
		console.log(file);
		if (!file) {
			console.error('No file selected!');
			return;
		}
	};

	let { value = $bindable(), inputDescription }: { value: string[]; inputDescription: string } =
		$props();
	$inspect({ value, inputDescription });
</script>

<div class="grid w-full max-w-sm items-center gap-1.5">
	<Label for="ids-file">{inputDescription}</Label>
	<Dialog.Root>
		<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>Add</Dialog.Trigger>
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
				<FileInput oninput={handleFileInput} id="ids-file" type="file" />
			</div>
		</Dialog.Content>
	</Dialog.Root>
</div>
