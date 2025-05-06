<script lang="ts">
	import TaskProgressDisplay from './task-progress-display.svelte';
	import { fetchTaskProgress } from '$lib/client-api/scrapers/tasks/progress';
	import { createQuery } from '@tanstack/svelte-query';

	let { scraperId, scraperTaskId }: { scraperId: number; scraperTaskId: number } = $props();

	let query = $derived(
		createQuery({
			queryKey: [`${scraperId}/${scraperTaskId}/progress`],
			queryFn: () => fetchTaskProgress(scraperId, scraperTaskId)
		})
	);
</script>

{#if $query.isLoading}
	<p>Loading...</p>
{:else if $query.isError}
	<p>Error: {$query.error.message}</p>
{:else if $query.isSuccess}
	{@const response = $query.data}
	{#if response.status === 'error'}
		<p>Error (HTTP Code {response.httpCode}): {response.message}</p>
	{:else}
		<TaskProgressDisplay progress={response.data} />
	{/if}
{/if}
