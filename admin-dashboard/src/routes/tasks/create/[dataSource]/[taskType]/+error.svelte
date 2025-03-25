<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
</script>

<PageHeading
	heading="Oops..."
	text="Looks like no task exists for this data source and task type."
/>
<div><Button href="/tasks/create">Back to Create Task</Button></div>
