<script lang="ts">
	import type { TaskQueueType } from '$lib/types-and-schemas/tasks/common';
	import * as Tabs from '$lib/components/ui/tabs';
	import QueueItemList from './queue-item-list.svelte';

	let { scraperId, scraperTaskId }: { scraperId: number; scraperTaskId: number } = $props();

	const queueTypes: readonly TaskQueueType[] = [
		'inputs',
		'successes',
		'failures',
		'inputs-without-output'
	];

	const tabLabels: Record<TaskQueueType, string> = {
		inputs: 'Remaining Inputs',
		successes: 'Successes',
		failures: 'Failures',
		'inputs-without-output': 'Inputs without Output'
	};

	let totals: Record<TaskQueueType, number | null> = $state({
		inputs: null,
		successes: null,
		failures: null,
		'inputs-without-output': null
	});
</script>

<Tabs.Root value={queueTypes[0]} class="w-full">
	<Tabs.List class="grid w-full grid-cols-4">
		{#each queueTypes as tab}
			<Tabs.Trigger value={tab}>
				{tabLabels[tab]}{totals[tab] !== null ? ` (${totals[tab]})` : ''}
			</Tabs.Trigger>
		{/each}
	</Tabs.List>
	{#each queueTypes as queueType}
		<Tabs.Content value={queueType}>
			<QueueItemList
				{queueType}
				{scraperId}
				{scraperTaskId}
				onTotalChange={(newTotal) => (totals[queueType] = newTotal)}
			/>
		</Tabs.Content>
	{/each}
</Tabs.Root>
