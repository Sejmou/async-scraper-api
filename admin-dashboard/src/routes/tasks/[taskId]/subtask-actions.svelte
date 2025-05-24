<script lang="ts">
	import {
		executeDisctributedTask,
		pauseDistributedTask
	} from '$lib/client-api/distributed-tasks/state-management';
	import Button from '$lib/components/ui/button/button.svelte';
	import Play from 'lucide-svelte/icons/play';
	import Pause from 'lucide-svelte/icons/pause';

	let { taskId }: { taskId: number } = $props();

	let handleClickExecuteAll = $derived(async () => {
		await executeDisctributedTask(taskId);
	});

	let handleClickPauseAll = $derived(async () => {
		await pauseDistributedTask(taskId);
	});
</script>

<div class="flex gap-2">
	<Button variant="outline" onclick={handleClickExecuteAll}><Play />Execute All</Button>
	<Button variant="outline" onclick={handleClickPauseAll}><Pause /> Pause All</Button>
</div>
