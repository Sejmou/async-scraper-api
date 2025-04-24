<script lang="ts">
	import * as Alert from '$lib/components/ui/alert';
	import CircleAlert from 'lucide-svelte/icons/circle-alert';
	import Info from 'lucide-svelte/icons/info';
	import type { Message } from '.';

	let { type, title, text, class: className = '' }: Message & { class?: string } = $props();
</script>

<Alert.Root class={className} variant={type === 'error' ? 'destructive' : 'default'}>
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
	<Alert.Description class="whitespace-pre">
		{text}
	</Alert.Description>
</Alert.Root>
