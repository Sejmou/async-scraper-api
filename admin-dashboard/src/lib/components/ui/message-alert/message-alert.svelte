<script lang="ts">
	import * as Alert from '$lib/components/ui/alert';
	import CircleAlert from 'lucide-svelte/icons/circle-alert';
	import Info from 'lucide-svelte/icons/info';
	import type { Message } from '.';

	let { type, text }: Message = $props();
</script>

<Alert.Root variant={type === 'error' ? 'destructive' : 'default'}>
	{#if type === 'error'}
		<CircleAlert class="h-4 w-4" />
	{:else}
		<Info class="h-4 w-4" />
	{/if}
	<Alert.Title>
		{#if type === 'error'}Error{:else}Heads up!{/if}
	</Alert.Title>
	<Alert.Description>{text}</Alert.Description>
</Alert.Root>
