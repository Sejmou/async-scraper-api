<script lang="ts">
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import Form from './form.svelte';

	let { data } = $props();
</script>

<PageHeading
	heading="Spotify Artists"
	text="Fetch metadata for artists from Spotify's public API."
/>
<Form artistsPayloadForm={data.artistsPayloadForm} />
