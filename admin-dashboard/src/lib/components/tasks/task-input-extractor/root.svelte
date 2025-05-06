<script lang="ts" generics="T extends z.ZodSchema">
	import Button from '$lib/components/ui/button/button.svelte';
	import { FileInputExtractor } from './file-input-extractor';
	import TextareaInputExtractor from './textarea-input-extractor.svelte';
	import { z } from 'zod';
	import { type InputExtractorProps, InputExtractorState } from './index.svelte';
	import InputsViewer from './inputs-viewer.svelte';

	let props: InputExtractorProps<T> = $props();

	let ieState = new InputExtractorState(props);

	let { inputsDescription } = props;

	let importMethod: 'file' | 'textarea' | null = $state(null);

	let viewingImportedInputs = $state(false);
</script>

<div class="flex w-full flex-col gap-2">
	{#if ieState.inputs.length > 0}
		<div class="flex w-full items-start justify-between">
			<p class="text-sm text-muted-foreground">
				{ieState.inputs.length}
				{inputsDescription} added.
			</p>
			<div class="flex gap-2">
				<Button variant="outline" onclick={() => (viewingImportedInputs = true)}>View</Button>
				<Button variant="destructive" onclick={() => (ieState.inputs = [])}>Reset</Button>
			</div>
		</div>
	{:else if importMethod !== null}
		<div class="flex w-full items-start justify-between">
			<span class="text-sm text-muted-foreground">
				{importMethod === 'file'
					? 'You have chosen to extract inputs from a file.'
					: 'You have chosen to enter inputs manually.'}
			</span>
			<Button variant="outline" onclick={() => (importMethod = null)}>Change method</Button>
		</div>
		{#if importMethod === 'file'}<FileInputExtractor {ieState} />
		{:else if importMethod === 'textarea'}
			<TextareaInputExtractor {ieState} />
		{/if}
	{:else}
		<p class="text-sm text-muted-foreground">
			{inputsDescription} can be added in multiple ways. Pick the one that suits you best!
		</p>
		<div class="flex w-full flex-col gap-4 lg:flex-row">
			<button
				class="rounded border px-8 py-4 hover:bg-secondary lg:w-1/2"
				onclick={() => (importMethod = 'file')}
			>
				<h2 class="text-center font-semibold">File</h2>
				<p class="text-center text-sm text-muted-foreground">
					Upload a file containing the data you want to extract (with a custom DuckDB SQL query, if
					needed).
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

	<InputsViewer {ieState} bind:open={viewingImportedInputs} />
</div>
