<script lang="ts">
	import PageHeading from '$lib/components/ui/page-heading.svelte';
</script>

<PageHeading heading="Create Task" text="Create a new task to execute on your scrapers." />

<h2 class="text-lg font-semibold">Data Sources</h2>
<ul class="list-disc pl-4">
	<li>
		<a class="text-sm text-blue-500 hover:underline" href="/tasks/create/spotify-api">
			Spotify API
		</a>
	</li>
	<li>
		<a class="text-sm text-blue-500 hover:underline" href="/tasks/create/spotify-internal">
			Internal (unofficial) Spotify APIs
		</a>
	</li>
	<li>
		<a class="text-sm text-blue-500 hover:underline" href="/tasks/create/dummy-api">
			Dummy API (for testing)
		</a>
	</li>
</ul>
