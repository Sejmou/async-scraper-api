<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import { Input } from '$lib/components/ui/input';
	import { formSchemaSingleInsert, type FormSchemaSingleInsert } from './form-schema';
	import { type SuperValidated, type Infer, superForm } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { MessageAlert } from '$lib/components/ui/message-alert';

	let { singleInsertForm }: { singleInsertForm: SuperValidated<Infer<FormSchemaSingleInsert>> } =
		$props();

	const form = superForm(singleInsertForm, {
		validators: zodClient(formSchemaSingleInsert)
	});

	const { form: formData, enhance } = form;

	let message = $state(form.message);
</script>

<form method="POST" action="?/add-one" use:enhance>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert {type} {text} />
	{/if}
	<Form.Field {form} name="baseUrl">
		<Form.Control>
			{#snippet children({ props })}
				<Form.Label>Base URL</Form.Label>
				<Input placeholder="http://192.0.2.1:8000" {...props} bind:value={$formData.baseUrl} />
			{/snippet}
		</Form.Control>
		<Form.Description>Please include protocol (http/https), domain, and port.</Form.Description>
		<Form.FieldErrors />
	</Form.Field>
	<Form.Button>Add</Form.Button>
</form>
