<script lang="ts">
	let { online }: { online: boolean } = $props();
</script>

<div class="flex items-center space-x-2">
	<div class="h-3 w-3 rounded-full" class:!bg-green-500={online} class:!bg-red-500={!online}></div>
	<span>{online ? 'Online' : 'Offline'}</span>
</div>
