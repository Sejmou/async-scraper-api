<script lang="ts" generics="T extends z.ZodSchema">
	import { z } from 'zod';
	import type { InputExtractorProps } from './input-extractor/index.svelte';
	import { InputExtractor } from './input-extractor/index.svelte';

	let {
		inputs,
		inputDescription,
		...rest
	}: InputExtractorProps<T> & {
		inputs: z.infer<T>[];
	} = $props();
</script>

<h2 class="text-2xl font-bold">Inputs ({inputDescription})</h2>
<p class="text-sm text-muted-foreground">
	{inputDescription} can be added in multiple ways. Pick the one that suits you best!
</p>
{#if inputs.length > 0}
	<InputExtractor {inputDescription} {...rest} />
{/if}
