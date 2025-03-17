<script lang="ts">
	import { type ScraperProgressData } from '.';

	let { progress }: { progress: ScraperProgressData } = $props();
</script>

{#await progress}
	<p>Loading...</p>
{:then progressData}
	{#if progressData === null}
		<p>No data. Probably an error.</p>
	{:else}
		<pre>{JSON.stringify(progressData, null, 2)}</pre>
	{/if}
{:catch error}
	<p>Error: {error.message}</p>
{/await}
