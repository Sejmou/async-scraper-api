<!-- fyi: This script block needs to be here to make TS syntax work for #snippet, even if we don't import anything -->
<script lang="ts">
	import PageHeading from '$lib/components/ui/page-heading.svelte';
</script>

<svelte:head>
	<title>Tasks</title>
</svelte:head>

<PageHeading heading="Tasks" text="Create tasks for your scrapers and monitor their progress." />
{#snippet infobox(label: string, description: string)}
	<a class="rounded border px-8 py-4 hover:bg-secondary lg:w-1/2" href="/tasks/create">
		<h2 class="text-center font-semibold">{label}</h2>
		<p class="text-center text-sm text-muted-foreground">{description}</p>
	</a>
{/snippet}
<div class="flex w-full flex-col gap-4 lg:flex-row">
	{@render infobox('Create', 'Create a new task')}
	{@render infobox('View', 'View your created tasks')}
</div>
