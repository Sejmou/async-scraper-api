<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import {
		artistsPayloadSchema,
		type ArtistsPayloadSchema
	} from '$lib/scraper-task-schemas/spotify-api';
	import { type SuperValidated, type Infer, superForm } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import InputExtractor from '$lib/components/input-extractor/input-extractor.svelte';

	let { artistsPayloadForm }: { artistsPayloadForm: SuperValidated<Infer<ArtistsPayloadSchema>> } =
		$props();

	const form = superForm(artistsPayloadForm, {
		validators: zodClient(artistsPayloadSchema)
	});

	const { form: formData, enhance } = form;

	let message = $state(form.message);
</script>

<form method="POST" use:enhance>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert {type} {text} />
	{/if}
	<Form.Field {form} name="artist_ids">
		<Form.Control>
			{#snippet children({ props })}
				<InputExtractor
					{...props}
					bind:value={$formData.artist_ids}
					inputDescription="Artist IDs"
				/>
			{/snippet}
		</Form.Control>
		<Form.Description>The artist IDs for which metadata should be loaded.</Form.Description>
		<Form.FieldErrors />
	</Form.Field>
	<Form.Button>Add</Form.Button>
</form>
