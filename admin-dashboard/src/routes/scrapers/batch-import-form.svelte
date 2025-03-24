<script lang="ts">
	import { Textarea } from '$lib/components/ui/textarea';
	import { enhance } from '$app/forms';
	import * as Form from '$lib/components/ui/form';
	import { formSchemaBatchImport, type FormSchemaBatchImport } from './form-schema';
	import { type SuperValidated, type Infer, superForm } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { MessageAlert } from '$lib/components/ui/message-alert';

	let {
		batchImportForm,
		onSubmitSuccess
	}: {
		batchImportForm: SuperValidated<Infer<FormSchemaBatchImport>>;
		onSubmitSuccess: () => void;
	} = $props();

	const form = superForm(batchImportForm, {
		validators: zodClient(formSchemaBatchImport),
		onUpdated: ({ form }) => {
			if (!form.message || form.message.type === 'success') {
				onSubmitSuccess();
			}
		}
	});

	const { form: formData } = form;

	let message = $state(form.message);
</script>

<form method="POST" action="?/batch-import" use:enhance>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert {type} {text} />
	{/if}
	<Form.Field {form} name="baseUrls">
		<Form.Control>
			{#snippet children({ props })}
				<Form.Label>Base URLs</Form.Label>
				<Textarea placeholder="http://192.0.2.1:8000" {...props} bind:value={$formData.baseUrls} />
			{/snippet}
		</Form.Control>
		<Form.Description
			>Add one URL per line. Please include protocol (http/https), domain, and port.</Form.Description
		>
		<Form.FieldErrors />
	</Form.Field>
	<div class="flex w-full justify-end">
		<Form.Button>Import</Form.Button>
	</div>
</form>
