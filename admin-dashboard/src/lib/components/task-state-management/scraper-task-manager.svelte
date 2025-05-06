<script lang="ts">
	import { fetchTaskMetadata } from '$lib/client-api/scrapers/tasks';
	import { pauseTask, resumeTask } from '$lib/client-api/scrapers/tasks/state-management';
	import TaskStatus from './task-status.svelte';
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';

	const queryClient = useQueryClient();

	let { scraperId, scraperTaskId }: { scraperId: number; scraperTaskId: number } = $props();
	let queryKey = $derived([scraperId, scraperTaskId, 'status']);

	let statusQuery = $derived(
		createQuery({
			queryKey,
			queryFn: () => fetchTaskMetadata(scraperId, scraperTaskId)
		})
	);

	let pauseMutation = $derived(
		createMutation({
			mutationFn: () => pauseTask(scraperId, scraperTaskId),
			onSuccess: (data) => {
				queryClient.setQueryData(queryKey, data);
			}
		})
	);

	let resumeMutation = $derived(
		createMutation({
			mutationFn: () => resumeTask(scraperId, scraperTaskId),
			onSuccess: (data) => {
				queryClient.setQueryData(queryKey, data);
			}
		})
	);
</script>

{#if $statusQuery.isLoading}
	<p>Loading...</p>
{:else if $statusQuery.isError}
	<p>Error: {$statusQuery.error.message}</p>
{:else if $statusQuery.isSuccess}
	{@const response = $statusQuery.data}
	{#if response.status === 'error'}
		<p>Error (HTTP Code {response.httpCode}): {response.message}</p>
	{:else}
		<TaskStatus
			status={response.data.status}
			onPause={$pauseMutation.mutate}
			onResume={$resumeMutation.mutate}
		/>
	{/if}
{/if}
