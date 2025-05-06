<script lang="ts">
	import ScraperTaskProgress from '$lib/components/task-state-management/task-progress-display.svelte';
	import type { TaskProgress } from '$lib/types-and-schemas/tasks/common';

	let {
		progressPromise,
		scraperCount
	}: { progressPromise: Promise<TaskProgress>; scraperCount: number } = $props();

	let scraperDesc = $derived(scraperCount > 1 ? `${scraperCount} scrapers` : '1 scraper');
</script>

{#if scraperCount > 0}
	{#await progressPromise}
		Loading...
	{:then progress}
		<ScraperTaskProgress
			{progress}
			dataDescSingular={`item (${scraperDesc})`}
			dataDescPlural={`items (${scraperDesc})`}
		/>
	{:catch}
		<span>Error while fetching</span>
	{/await}
{:else}
	<span class="text-sm text-muted-foreground">No scrapers/subtasks?!</span>
{/if}
