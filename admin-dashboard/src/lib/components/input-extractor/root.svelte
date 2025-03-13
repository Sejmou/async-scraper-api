<script lang="ts" generics="TSchema extends z.ZodSchema">
	import type { JSONSerializableValue } from '$lib/utils';
	import { Label } from '../ui/label';
	import * as Dialog from '../ui/dialog';
	import { buttonVariants } from '../ui/button';
	import Button from '../ui/button/button.svelte';
	import { FileInputExtractor } from './file';
	import { z } from 'zod';

	type Input = z.infer<TSchema>;
	let inputs: Input[] = [];

	let {
		onInputsExtracted,
		inputDescription
	}: {
		onInputsExtracted: (inputs: Input[]) => void;
		inputSchema: z.ZodSchema;
		inputDescription: string;
	} = $props();

	let importMethod: 'file' | 'textarea' | null = $state(null);
</script>

<div class="grid w-full max-w-sm items-center gap-1.5">
	<Label for="ids-file">{inputDescription}</Label>
	<Dialog.Root>
		<Dialog.Trigger class={buttonVariants({ variant: 'outline' })}>Add</Dialog.Trigger>
		<Dialog.Content class="flex max-h-[80vh] max-w-screen-md flex-col">
			<Dialog.Header>
				<Dialog.Title>Add {inputDescription}</Dialog.Title>
				<Dialog.Description>
					{inputDescription} can be added in multiple ways. Pick the one that suits you best!
				</Dialog.Description>
			</Dialog.Header>
			<div class="flex w-full flex-col gap-4 overflow-y-auto pr-2">
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
						<FileInputExtractor />
					{/if}
				{:else}
					<div class="flex w-full flex-col gap-4 lg:flex-row">
						<button
							class="rounded border px-8 py-4 hover:bg-secondary lg:w-1/2"
							onclick={() => (importMethod = 'file')}
						>
							<h2 class="text-center font-semibold">File</h2>
							<p class="text-center text-sm text-muted-foreground">
								Upload a file containing the data you want to extract. If necessary, you can use
								DuckDB SQL to specify how exactly the data should be extracted (e.g. if data types
								don't match).
							</p>
						</button>
						<button
							class="rounded border px-8 py-4 hover:bg-secondary lg:w-1/2"
							onclick={() => (importMethod = 'textarea')}
						>
							<h2 class="text-center font-semibold">Enter manually (or copy-paste)</h2>
							<p class="text-center text-sm text-muted-foreground">
								Enter the data line-by-line. It will be converted into the proper format
								automatically.
							</p>
						</button>
					</div>
				{/if}
			</div>
			<Dialog.Footer>
				<Button
					type="submit"
					disabled={inputs.length === 0}
					onclick={() => onInputsExtracted(inputs)}
				>
					Add
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Root>
</div>
