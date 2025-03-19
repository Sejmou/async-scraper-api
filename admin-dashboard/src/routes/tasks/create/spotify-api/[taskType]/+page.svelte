<script lang="ts">
	import NewTaskForm from '$lib/components/new-task-form/new-task-form.svelte';

	let { data } = $props();
	let { initialTaskValue, paramsSchema, taskInputMeta } = $derived(data);
</script>

<NewTaskForm {initialTaskValue} {paramsSchema} {taskInputMeta} />
