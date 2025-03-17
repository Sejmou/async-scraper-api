<script lang="ts">
	import SubtaskInfo from '../subtask-info.svelte';

	let { data } = $props();
	let task = $derived(data.task);
</script>

<h2 class="text-2xl font-semibold">Task details</h2>
<ul class="list-disc pl-4">
	<li>ID: {task.id}</li>
	<li>Data source: {task.dataSource}</li>
	<li>Task type: {task.taskType}</li>
	<li>
		{#if task.params}Parameters: {JSON.stringify(task.params)}{:else}No parameters{/if}
	</li>
</ul>
<h3 class="text-lg font-semibold">Subtasks</h3>
<div>
	<SubtaskInfo subtasks={task.subtasks} />
</div>
