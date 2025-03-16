<script lang="ts">
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import Form from './form.svelte';

	let { data } = $props();
</script>

<PageHeading heading="Spotify Tracks" text="Fetch metadata for tracks from Spotify's public API." />
<Form tracksForm={data.tracksForm} />
