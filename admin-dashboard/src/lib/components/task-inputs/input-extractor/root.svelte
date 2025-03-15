<script lang="ts" generics="T extends z.ZodSchema">
	import Button from '../../ui/button/button.svelte';
	import { FileInputExtractor } from './file';
	import { z } from 'zod';
	import { type InputExtractorProps, InputExtractorState } from './index.svelte';

	let inputs: z.infer<T>[] = [];

	const props: InputExtractorProps<T> = $props();
	const ieState = new InputExtractorState(props);

	let { inputDescription } = props;

	let importMethod: 'file' | 'textarea' | null = $state(null);
</script>

{#if importMethod !== null}
	<div class="flex w-full items-center justify-between">
		<span class="text-sm">
			{importMethod === 'file'
				? 'You have chosen to extract inputs from a file.'
				: 'You have chosen to enter inputs manually.'}
		</span>
		<Button variant="outline" onclick={() => (importMethod = null)}>Change method</Button>
	</div>
	{#if importMethod === 'file'}
		<FileInputExtractor {ieState} />
	{/if}
	{#if inputs.length > 0}
		<p class="text-sm text-muted-foreground">
			{inputs.length}
			{inputDescription} extracted.
		</p>
		<Button variant="outline">Preview</Button>
	{/if}
{:else}
	<div class="flex w-full flex-col gap-4 lg:flex-row">
		<button
			class="rounded border px-8 py-4 hover:bg-secondary lg:w-1/2"
			onclick={() => (importMethod = 'file')}
		>
			<h2 class="text-center font-semibold">File</h2>
			<p class="text-center text-sm text-muted-foreground">
				Upload a file containing the data you want to extract. If necessary, you can use DuckDB SQL
				to specify how exactly the data should be extracted (e.g. if data types don't match).
			</p>
		</button>
		<button
			class="rounded border px-8 py-4 hover:bg-secondary lg:w-1/2"
			onclick={() => (importMethod = 'textarea')}
		>
			<h2 class="text-center font-semibold">Enter manually (or copy-paste)</h2>
			<p class="text-center text-sm text-muted-foreground">
				Enter the data line-by-line. It will be converted into the proper format automatically.
			</p>
		</button>
	</div>
{/if}
