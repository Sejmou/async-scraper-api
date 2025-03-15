<script lang="ts" generics="T extends z.ZodSchema">
	import { z } from 'zod';
	import type { InputExtractorState } from './index.svelte';

	let { ieState }: { ieState: InputExtractorState<T>; inputsValid: boolean } = $props();
	let { inputSchema } = ieState;
</script>
