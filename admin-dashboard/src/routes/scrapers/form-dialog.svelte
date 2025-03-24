<script lang="ts">
	import { buttonVariants } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { Label } from '$lib/components/ui/label';
	import BatchImportForm from './batch-import-form.svelte';
	let batchImport = $state(false);

	import type { Infer, SuperValidated } from 'sveltekit-superforms';
	import Form from './single-insert-form.svelte';
	import type { FormSchemaBatchImport, FormSchemaSingleInsert } from './form-schema';

	let {
		data
	}: {
		data: {
			singleInsertForm: SuperValidated<Infer<FormSchemaSingleInsert>>;
			batchInsertForm: SuperValidated<Infer<FormSchemaBatchImport>>;
		};
	} = $props();

	let singleInsertForm = data.singleInsertForm;
	let batchImportForm = data.batchInsertForm;

	let dialogOpen = $state(false);

	const handleSuccess = () => {
		dialogOpen = false;
	};
</script>

<Dialog.Root bind:open={dialogOpen}>
	<div class="flex w-full justify-end">
		<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>Add</Dialog.Trigger>
	</div>
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
			<BatchImportForm {batchImportForm} onSubmitSuccess={handleSuccess} />
		{:else}
			<Form {singleInsertForm} onSubmitSuccess={handleSuccess} />
		{/if}
	</Dialog.Content>
</Dialog.Root>
