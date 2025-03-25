<script lang="ts">
	import { z } from 'zod';
	import { setTaskFormState } from '$lib/components/new-task-form/index.svelte.js';
	import NewTaskForm from '$lib/components/new-task-form/new-task-form.svelte';

	let { data } = $props();

	setTaskFormState(data.initialTaskValue, data.paramsSchema || z.object({}), data.taskInputMeta);
</script>

<NewTaskForm />
