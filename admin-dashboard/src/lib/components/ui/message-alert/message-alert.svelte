<script lang="ts">
	import * as Alert from '$lib/components/ui/alert';
	import CircleAlert from 'lucide-svelte/icons/circle-alert';
	import Info from 'lucide-svelte/icons/info';
	import type { Message } from '.';

	let { type, title, text }: Message = $props();
	let lines = text.split('\n');
</script>

<Alert.Root variant={type === 'error' ? 'destructive' : 'default'}>
	{#if type === 'error'}
		<CircleAlert class="h-4 w-4" />
	{:else}
		<Info class="h-4 w-4" />
	{/if}
	<Alert.Title>
		{#if title}
			{title}
		{:else if type === 'error'}
			Error
		{:else}
			Heads up!
		{/if}
	</Alert.Title>
	<Alert.Description
		>{#each lines as line}
			{line}
			{#if line !== lines[lines.length - 1]}
				<br />
			{/if}
		{/each}
	</Alert.Description>
</Alert.Root>
