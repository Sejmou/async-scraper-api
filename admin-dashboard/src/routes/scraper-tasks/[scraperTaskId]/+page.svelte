<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import * as Card from '$lib/components/ui/card';
	import ScraperTaskProgressTracker from '$lib/components/tasks/scraper-task-progress-tracker.svelte';
	import ScraperTaskManager from '$lib/components/tasks/scraper-task-manager.svelte';
	import TaskLogViewer from '$lib/components/tasks/task-log-viewer.svelte';
	import { TaskQueueItemManager } from '$lib/components/tasks/task-queue-item-manager';

	let { data } = $props();

	let scraperTask = $derived(data.scraperTask);
</script>

<PageHeading
	heading="Scraper Task {scraperTask.id}"
	text="Details for a subtask of a distributed task you created, running on one of your scrapers."
/>

<Card.Root>
	<Card.Header>
		<Card.Title>Parent Task</Card.Title>
		<Card.Description>
			The task this task is a subtask of. All subtasks of the parent task share the same parameters,
			only the inputs differ.
		</Card.Description>
	</Card.Header>
	<Card.Content>
		<p class="text-sm">
			<code>{scraperTask.task.dataSource}/{scraperTask.task.taskType}</code>, created at {scraperTask
				.task.createdAt}
		</p>
		<h4 class="mt-4 font-semibold">Parameters</h4>
		<pre class="text-sm">
        {scraperTask.task.params
				? JSON.stringify(scraperTask.task.params, null, 2)
				: 'No parameters'}
      </pre>
	</Card.Content>
	<Card.Footer>
		<Button variant="outline" href="/tasks/{scraperTask.task.id}">View</Button>
	</Card.Footer>
</Card.Root>
<Card.Root>
	<Card.Header>
		<Card.Title>Task on Scraper</Card.Title>
		<Card.Description>Metadata related to the scraper the task is running on.</Card.Description>
	</Card.Header>
	<Card.Content>
		<h4 class="text-md font-semibold">Scraper URL</h4>
		<p class="text-sm text-muted-foreground">
			{scraperTask.scraper.protocol}://{scraperTask.scraper.host}:{scraperTask.scraper.port}
		</p>
		<h4 class="text-md mt-2 font-semibold">Task ID on scraper</h4>
		<p class="text-sm text-muted-foreground">
			<code>{scraperTask.scraperTaskId}</code>
		</p>
	</Card.Content>
	<Card.Footer>
		<Button variant="outline" href="/scrapers/{scraperTask.scraper.id}">
			View Scraper Details
		</Button>
	</Card.Footer>
</Card.Root>

<div class="flex justify-between gap-4">
	<Card.Root class="w-1/2">
		<Card.Header>
			<Card.Title>Status</Card.Title>
			<Card.Description>
				The current status of the task. You can also pause/resume if possible.
			</Card.Description>
		</Card.Header>
		<Card.Content>
			<ScraperTaskManager
				scraperId={scraperTask.scraperId}
				scraperTaskId={scraperTask.scraperTaskId}
			/>
		</Card.Content>
	</Card.Root>
	<Card.Root class="w-1/2">
		<Card.Header>
			<Card.Title>Progress</Card.Title>
			<Card.Description>
				The progress the scraper has made trying to process the inputs you gave it. Click on the bar
				to view details.
			</Card.Description>
		</Card.Header>
		<Card.Content>
			<ScraperTaskProgressTracker
				scraperId={scraperTask.scraperId}
				scraperTaskId={scraperTask.scraperTaskId}
			/>
		</Card.Content>
	</Card.Root>
</div>

<h3 class="mt-4 text-xl font-semibold">Inputs</h3>
<TaskQueueItemManager scraperId={scraperTask.scraperId} scraperTaskId={scraperTask.scraperTaskId} />

<TaskLogViewer scraperId={scraperTask.scraperId} scraperTaskId={scraperTask.scraperTaskId} />
