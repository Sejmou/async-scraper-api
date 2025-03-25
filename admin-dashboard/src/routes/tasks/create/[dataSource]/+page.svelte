<script lang="ts">
	import PageHeading from '$lib/components/ui/page-heading.svelte';

	let { data } = $props();
	let dataSource = $derived(data.dataSource);
	let taskCreatePages = $derived(data.taskCreatePages);
</script>

<PageHeading heading={dataSource.name} text={dataSource.description} />

<h2 class="text-lg font-semibold">Endpoints</h2>
<ul class="list-disc pl-4">
	{#each taskCreatePages as { href, label }}
		<li>
			<a class="text-sm text-blue-500 hover:underline" {href}>{label}</a>
		</li>
	{/each}
</ul>
