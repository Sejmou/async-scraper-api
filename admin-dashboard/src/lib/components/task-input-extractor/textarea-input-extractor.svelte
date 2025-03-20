<script lang="ts" generics="T extends z.ZodSchema">
	import { z } from 'zod';
	import { Textarea } from '$lib/components/ui/textarea';
	import { type InputExtractorState } from './index.svelte';
	import { Button } from '../ui/button';
	import type { Message } from '$lib/components/ui/console-message-alert';
	import { ConsoleMessageAlert } from '$lib/components/ui/console-message-alert';

	let { ieState }: { ieState: InputExtractorState<T> } = $props();
	let parseInputFromJSON = $derived(typeof ieState.exampleInput !== 'string');

	let inputStr = $state('');

	let validating = $state(false);
	let message: Message | null = $state(null);

	let handleImportClick = async () => {
		if (validating) return;
		validating = true;
		let strs = inputStr.split('\n');
		const parsedData: z.infer<T>[] = [];

		for (const [i, str] of strs.entries()) {
			if (str.trim() === '') continue;

			let data = str;
			if (parseInputFromJSON) {
				try {
					data = JSON.parse(str);
				} catch {
					message = {
						type: 'error',
						title: 'Error validating inputs',
						text: `Could not parse data to JSON at line ${i + 1}. Please make sure the data is in valid JSON format`
					};
					return;
				}
			}

			const result = ieState.inputSchema.safeParse(data);
			if (result.success) {
				parsedData.push(result.data);
			} else {
				message = {
					type: 'error',
					title: 'Error validating inputs',
					text:
						`Element at line ${i + 1} could is invalid:\n` +
						result.error.issues.map((issue) => issue.message).join('\n')
				};
			}
		}
		validating = false;
		ieState.inputs = parsedData;
	};

	function handleKeydown(event: KeyboardEvent) {
		// Check if the user pressed "Enter"
		if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
			event.preventDefault(); // Prevent default behavior if necessary
			handleImportClick();
		}
	}
</script>

<div class="flex w-full flex-col">
	<h3 class="font-semibold">Enter/Copy-paste Data</h3>
	<p class="text-sm text-muted-foreground">
		Enter the data you want to extract in the text area below. The {ieState.inputDescription} should
		be provided
		{parseInputFromJSON ? ' in JSON lines format (one per line' : ' on separate lines'}.
	</p>
	<p class="mt-2 text-sm text-muted-foreground">Example:</p>
	<pre class="my-2 ml-4 text-sm text-muted-foreground">{JSON.stringify(
			ieState.exampleInput,
			null,
			2
		)}</pre>
	{#if message}
		<ConsoleMessageAlert {...message} />
	{/if}
	<Textarea
		placeholder={`Enter ${ieState.inputDescription} here...`}
		bind:value={inputStr}
		rows={10}
		onkeydown={handleKeydown}
	/>
	<div class="mt-4 flex w-full justify-end">
		<Button disabled={!inputStr.trim()} onclick={handleImportClick}
			>Import Data (Ctrl + Enter)</Button
		>
	</div>
</div>
