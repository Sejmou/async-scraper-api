<script lang="ts">
	import FileInput from './ui/file-input/file-input.svelte';
	import { Label } from './ui/label';

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

	let { value = $bindable(), idDescription }: { value: string[]; idDescription: string } = $props();
	$inspect({ value, idDescription });
</script>

<h2 class="text-lg font-bold">{idDescription}</h2>
<div class="grid w-full max-w-sm items-center gap-1.5">
	<Label for="ids-file">Upload file with IDs</Label>
	<FileInput oninput={handleFileInput} id="ids-file" type="file" />
</div>
