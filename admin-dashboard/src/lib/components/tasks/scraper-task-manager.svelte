<script lang="ts">
	import { fetchTaskMetadata } from '$lib/client-api/scrapers/tasks';
	import { pauseTask, executeTask } from '$lib/client-api/scrapers/tasks/state-management';
	import TaskStatus from './task-status.svelte';
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';

	const queryClient = useQueryClient();

	let { scraperId, scraperTaskId }: { scraperId: number; scraperTaskId: number } = $props();
	let queryKey = $derived([scraperId, scraperTaskId, 'status']);

	let statusQuery = $derived(
		createQuery({
			queryKey,
			queryFn: () => fetchTaskMetadata(scraperId, scraperTaskId),
			refetchInterval: 1000,
			refetchIntervalInBackground: false
		})
	);

	let pauseMutation = $derived(
		createMutation({
			mutationFn: () => pauseTask(scraperId, scraperTaskId),
			onSuccess: (data) => {
				console.log('Updating task status after pause', data);
				queryClient.setQueryData(queryKey, data);
			},
			onError: (error) => {
				console.error('Error pausing task:', error);
			},
			onMutate: () => {
				console.log('Pausing task...');
			},
			onSettled: () => {
				console.log('Task paused');
			}
		})
	);

	let resumeMutation = $derived(
		createMutation({
			mutationFn: () => executeTask(scraperId, scraperTaskId),
			onSuccess: (data) => {
				console.log('Updating task status after resume', data);
				queryClient.setQueryData(queryKey, data);
			},
			onError: (error) => {
				console.error('Error resuming task:', error);
			},
			onMutate: () => {
				console.log('Resuming task...');
			},
			onSettled: () => {
				console.log('Task resumed');
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
