<script lang="ts">
	import Ellipsis from '@lucide/svelte/icons/ellipsis';
	import ScrollText from '@lucide/svelte/icons/scroll-text';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import Button from '$lib/components/ui/button/button.svelte';

	let { scraperId, taskId }: { scraperId: number; taskId: number } = $props();
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger>
		{#snippet child({ props })}
			<Button {...props} variant="ghost" size="icon" class="relative size-8 p-0">
				<span class="sr-only">Open menu</span>
				<Ellipsis />
			</Button>
		{/snippet}
	</DropdownMenu.Trigger>
	<DropdownMenu.Content>
		<DropdownMenu.Group>
			<DropdownMenu.GroupHeading>Actions</DropdownMenu.GroupHeading>
			<a href={`/api/scrapers/${scraperId}/tasks/${taskId}/logs`} download>
				<DropdownMenu.Item>
					<ScrollText class="h-4 w-4" />
					Download Logs
				</DropdownMenu.Item>
			</a>
		</DropdownMenu.Group>
	</DropdownMenu.Content>
</DropdownMenu.Root>
