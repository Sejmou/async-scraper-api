<script lang="ts">
	import { buttonVariants } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { Label } from '$lib/components/ui/label';
	import BatchImportForm from './batch-import-form.svelte';
	let batchImport = $state(false);

	import type { Infer, SuperValidated } from 'sveltekit-superforms';
	import Form from './form.svelte';
	import type { FormSchema } from './form-schema';

	let { data }: { data: { form: SuperValidated<Infer<FormSchema>> } } = $props();
</script>

<Dialog.Root>
	<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>Add</Dialog.Trigger>
	<Dialog.Content class="max-w-screen-md">
		<Dialog.Header>
			<Dialog.Title>Add scraper(s)</Dialog.Title>
			<Dialog.Description>
				You can add one at a time or batch-import multiple scrapers.
			</Dialog.Description>
		</Dialog.Header>
		<div class="flex items-center space-x-2">
			<Checkbox id="batch-import" bind:checked={batchImport} aria-labelledby="batch-import-label" />
			<Label
				id="batch-import-label"
				for="batch-import"
				class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
			>
				Batch import
			</Label>
		</div>
		{#if batchImport}
			<BatchImportForm />
		{:else}
			<Form {data} />
		{/if}
	</Dialog.Content>
</Dialog.Root>
