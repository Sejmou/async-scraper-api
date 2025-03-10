<script lang="ts">
	const subpages: {
		label: string;
		href: string;
		description: string;
	}[] = [
		{ label: 'Scrapers', href: 'scrapers', description: 'Manage servers running the Scraper API' },
		{ label: 'Tasks', href: 'tasks', description: 'Schedule tasks on the scrapers' }
	];
</script>

<div class="flex h-screen items-center justify-center">
	<div class="flex w-full max-w-screen-md flex-col items-center gap-4">
		<h1 class="text-5xl font-bold">Welcome</h1>
		<div class="flex w-full justify-center gap-2">
			{#each subpages as { label, href, description }}
				<a class="w-1/2 rounded border px-8 py-4 hover:bg-secondary" {href}>
					<h2 class="text-center font-semibold">{label}</h2>
					<p class="text-center text-sm text-muted-foreground">{description}</p></a
				>
			{/each}
		</div>
	</div>
</div>
