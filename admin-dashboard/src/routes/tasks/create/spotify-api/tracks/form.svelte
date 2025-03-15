<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import {
		tracksPayloadSchema,
		type TracksPayloadSchema
	} from '$lib/scraper-task-schemas/spotify-api';
	import { type SuperValidated, type Infer, superForm } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import { InputExtractor } from '$lib/components/task-creator/input-extractor/index.svelte';
	import { z } from 'zod';

	let { tracksPayloadForm }: { tracksPayloadForm: SuperValidated<Infer<TracksPayloadSchema>> } =
		$props();

	const form = superForm(tracksPayloadForm, {
		validators: zodClient(tracksPayloadSchema)
	});

	const { form: formData, enhance } = form;

	let message = $state(form.message);
</script>

<form method="POST" use:enhance>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert {type} {text} />
	{/if}
	<Form.Field {form} name="track_ids">
		<Form.Control>
			{#snippet children({ props })}
				<InputExtractor
					{...props}
					inputDescription="Track IDs"
					exampleInput="4PTG3Z6ehGkBFwjybzWkR8"
					inputSchema={z.string()}
					onInputsAdded={(inputs) => ($formData.track_ids = inputs)}
					inputsTableName="sp_api_track_ids"
				/>
			{/snippet}
		</Form.Control>
		<Form.Description>The track IDs for which metadata should be loaded.</Form.Description>
		<Form.FieldErrors />
	</Form.Field>
	<Form.Button>Add</Form.Button>
</form>
