<script lang="ts">
	const subpages: {
		label: string;
		href: string;
		description: string;
	}[] = [
		{
			label: 'Scrapers',
			href: 'scrapers',
			description: 'Manage a cluster of servers running the Scraper API'
		},
		{
			label: 'Tasks',
			href: 'tasks',
			description: 'Schedule and monitor/manage tasks on the scrapers'
		}
	];
</script>

<div class="mx-auto flex w-full max-w-screen-md flex-col items-center gap-4">
	<h1 class="text-5xl font-bold">Welcome</h1>
	<div class="flex w-full flex-col justify-center gap-2 lg:flex-row">
		{#each subpages as { label, href, description }}
			<a class="rounded border px-8 py-4 hover:bg-secondary lg:w-1/2" {href}>
				<h2 class="text-center font-semibold">{label}</h2>
				<p class="text-center text-sm text-muted-foreground">{description}</p></a
			>
		{/each}
	</div>
</div>
