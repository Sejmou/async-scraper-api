<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
</script>

<PageHeading heading="Oops..." text="Looks like this task doesn't exist." />
<div><Button href="/tasks">Back to Task List</Button></div>
