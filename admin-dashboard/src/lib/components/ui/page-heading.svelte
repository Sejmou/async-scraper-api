<script lang="ts">
	let { heading, text }: { heading: string; text: string } = $props();
</script>

<h1 class="text-3xl font-bold">{heading}</h1>
<p class="text-sm text-muted-foreground">
	{text}
</p>
