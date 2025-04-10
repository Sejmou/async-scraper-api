<script lang="ts">
	import type { DataFetchingTaskStatus } from '$lib/scraper-types-and-schemas/created-tasks';
	import Play from 'lucide-svelte/icons/play';
	import Pause from 'lucide-svelte/icons/pause';
	import Button from '$lib/components/ui/button/button.svelte';
	import CheckMark from 'lucide-svelte/icons/check';
	let { status }: { status: DataFetchingTaskStatus } = $props();

	const titleCase = (str: string) => str[0].toUpperCase() + str.slice(1);
</script>

{#if status === 'done'}
	<div class="flex items-center gap-2 px-4 text-sm text-muted-foreground">
		<CheckMark class="h-4 w-4" />
		Done
	</div>
{:else}
	<Button variant={status === 'error' ? 'destructive' : 'outline'}>
		{#if status === 'paused' || status === 'error'}
			<Play class="h-4 w-4" />
		{:else if status === 'running' || status === 'pending'}
			<Pause class="h-4 w-4" />
		{/if}
		{titleCase(status)}
	</Button>
{/if}
