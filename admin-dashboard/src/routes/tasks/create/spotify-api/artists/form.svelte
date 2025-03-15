<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import {
		artistsPayloadSchema,
		type ArtistsPayloadSchema
	} from '$lib/scraper-task-schemas/spotify-api';
	import { type SuperValidated, type Infer, superForm } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import InputExtractor from '$lib/components/task-creator/input-extractor/root.svelte';
	import { z } from 'zod';

	let { artistsPayloadForm }: { artistsPayloadForm: SuperValidated<Infer<ArtistsPayloadSchema>> } =
		$props();

	const form = superForm(artistsPayloadForm, {
		validators: zodClient(artistsPayloadSchema)
	});

	const { form: formData, enhance } = form;

	let message = $state(form.message);
</script>

<form class="flex h-full w-full flex-col" method="POST" use:enhance>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert {type} {text} />
	{/if}
	<Form.Field {form} name="artist_ids">
		<Form.Control>
			{#snippet children({ props })}
				<InputExtractor
					{...props}
					inputDescription="Artist IDs"
					inputSchema={z.string()}
					exampleInput="06HL4z0CvFAxyc27GXpf02"
					onInputChange={(inputs) => {
						$formData.artist_ids = inputs;
					}}
					inputsTableName="sp_api_artist_ids"
				/>
			{/snippet}
		</Form.Control>
		<Form.FieldErrors />
	</Form.Field>
	{#if $formData.artist_ids.length > 0}
		<div class="flex w-full justify-end">
			<Form.Button disabled={$formData.artist_ids.length == 0} class="mt-auto"
				>Create Task</Form.Button
			>
		</div>
	{/if}
</form>
