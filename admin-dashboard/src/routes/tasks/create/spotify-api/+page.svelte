<script lang="ts">
	import PageHeading from '$lib/components/ui/page-heading.svelte';
</script>

<PageHeading
	heading="Create Spotify API task"
	text="Create tasks for fetching data from Spotify's public API."
/>

<h2 class="text-lg font-semibold">Spotify API Endpoints</h2>
<ul class="list-disc pl-4">
	<li>
		<a class="text-sm text-blue-500 hover:underline" href="/tasks/create/spotify-api/tracks"
			>Tracks</a
		>
	</li>
	<li>
		<a class="text-sm text-blue-500 hover:underline" href="/tasks/create/spotify-api/albums"
			>Albums</a
		>
	</li>
	<li>
		<a class="text-sm text-blue-500 hover:underline" href="/tasks/create/spotify-api/artists"
			>Artists</a
		>
	</li>
	<li>
		<a class="text-sm text-blue-500 hover:underline" href="/tasks/create/spotify-api/playlists">
			Playlists
		</a>
	</li>
</ul>
