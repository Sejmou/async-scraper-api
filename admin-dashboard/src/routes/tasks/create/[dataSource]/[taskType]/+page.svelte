<script lang="ts">
	import { z } from 'zod';
	import { setTaskFormState } from '$lib/components/tasks/new-task-form/index.svelte.js';
	import NewTaskForm from '$lib/components/tasks/new-task-form/new-task-form.svelte';

	let { data } = $props();

	setTaskFormState(
		data.scrapers,
		data.initialTaskValue,
		data.paramsSchema || z.object({}),
		data.taskInputMeta
	);
</script>

<NewTaskForm />
