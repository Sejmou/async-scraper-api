<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import CodeEditor from '$lib/components/code-editor.svelte';
	import {
		cn,
		currentTimestampToFilenameCompatibleString,
		downloadAsFile,
		timeAgoUTCDate
	} from '$lib/utils';
	import { Button } from '$lib/components/ui/button';
	import Download from 'lucide-svelte/icons/download';
	import RefreshCw from 'lucide-svelte/icons/refresh-cw';
	import { onMount } from 'svelte';

	let {
		scraperId,
		scraperTaskId,
		class: className
	}: { scraperId: number; scraperTaskId: number; class?: string } = $props();

	let queryKey = $derived([scraperId, scraperTaskId, 'logs']);

	let logFileQuery = $derived(
		createQuery({
			queryKey,
			queryFn: () =>
				fetch(`/api/scrapers/${scraperId}/tasks/${scraperTaskId}/logs`).then((response) => {
					if (!response.ok) {
						throw new Error('Network response was not ok');
					}
					return response.text();
				})
		})
	);

	let lastRefreshDate = $state(new Date());

	onMount(() => {
		const interval = setInterval(() => {
			lastRefreshDate = new Date($logFileQuery.dataUpdatedAt);
		}, 1000);

		return () => clearInterval(interval);
	});

	async function handleDownloadClick() {
		await $logFileQuery.refetch();
		const fileContents = $logFileQuery.data;
		if (!fileContents) {
			console.error('No file contents available to download');
			return;
		}
		downloadAsFile(
			fileContents,
			`scraper-${scraperId}_task-${scraperTaskId}_logs_${currentTimestampToFilenameCompatibleString()}`
		);
	}
</script>

{#if $logFileQuery.isLoading}
	<p>Loading...</p>
{:else if $logFileQuery.isError}
	<p>Error: {$logFileQuery.error.message}</p>
{:else if $logFileQuery.isSuccess}
	{@const fileContents = $logFileQuery.data}
	<h3 class="mt-4 text-xl font-semibold">
		Logs
		<Button class="ml-2" variant="outline" size="sm" onclick={handleDownloadClick}>
			<Download />
			Download
		</Button>
	</h3>
	<div class="flex w-full items-center justify-between">
		<span class="text-sm text-muted-foreground">
			Last update: {timeAgoUTCDate(lastRefreshDate)}
		</span>
		<Button variant="outline" size="sm" onclick={$logFileQuery.refetch}><RefreshCw />Refresh</Button
		>
	</div>
	<CodeEditor
		class={cn('min-h-[420px]', className)}
		value={fileContents}
		language="plaintext"
		readOnly
		scrollbarAlwaysConsumeMouseWheel
	/>
{/if}
