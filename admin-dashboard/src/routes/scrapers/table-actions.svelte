<script lang="ts">
	import Ellipsis from 'lucide-svelte/icons/ellipsis';
	import { Button } from '$lib/components/ui/button';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';

	import { enhance } from '$app/forms';

	let { id, host }: { id: number; host: string } = $props();
	let deleteDialogOpen = $state(false);
	// TODO: figure out smarter way to reset dialog state whenever id or host changes
	// without this code, dialog will remain open upon successful deletion
	$effect(() => {
		if (id || host) {
			deleteDialogOpen = false;
		}
	});
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
			<DropdownMenu.Item onSelect={() => (deleteDialogOpen = true)}>
				Delete
				<!-- <button class="w-full" onclick={() => (deleteDialogOpen = true)}>Delete</button> -->
			</DropdownMenu.Item>
		</DropdownMenu.Group>
	</DropdownMenu.Content>
</DropdownMenu.Root>

<AlertDialog.Root bind:open={deleteDialogOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete scraper</AlertDialog.Title>
			<AlertDialog.Description>
				Are you sure you want to delete the scraper at {host}?
			</AlertDialog.Description>
		</AlertDialog.Header>
		<form method="POST" action="?/delete" use:enhance>
			<AlertDialog.Footer>
				<AlertDialog.Cancel type="button">Cancel</AlertDialog.Cancel>
				<input type="hidden" name="id" value={id} />
				<AlertDialog.Action type="submit">Confirm</AlertDialog.Action>
			</AlertDialog.Footer>
		</form>
	</AlertDialog.Content>
</AlertDialog.Root>
