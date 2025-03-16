<script lang="ts">
	import { artistsPayloadSchema } from '$lib/scraper-task-schemas/spotify-api';
	import InputExtractor from '$lib/components/task-input-extractor/root.svelte';
	import PageHeading from '$lib/components/ui/page-heading.svelte';
	import { superForm, defaults } from 'sveltekit-superforms';
	import { zod } from 'sveltekit-superforms/adapters';
	import { MessageAlert, type Message } from '$lib/components/ui/message-alert';
	import * as Form from '$lib/components/ui/form';
	import { z } from 'zod';

	const form = superForm(defaults(zod(artistsPayloadSchema)), {
		SPA: true,
		validators: zod(artistsPayloadSchema),
		resetForm: false
	});

	const { form: formData, enhance, validateForm, errors } = form;

	async function handleSubmit(event: Event) {
		event.preventDefault();
		const result = await validateForm();

		if (!result.valid) {
			errors.update((v) => {
				return {
					...v,
					artist_ids: result.errors.artist_ids
				};
			});

			return;
		}

		// const success = await sendTask($formData.artist_ids);

		// if(success) {
		// 	return await goto('/')
		// }

		message = {
			type: 'success',
			text: 'Task created successfully!'
		};
	}

	let message: Message | null = $state(null);
	let artist_ids: string[] = [];
</script>

<PageHeading
	heading="Spotify Artists"
	text="Fetch metadata for artists from Spotify's public API."
/>

<InputExtractor
	inputDescription="Artist IDs"
	inputSchema={z.string()}
	exampleInput="06HL4z0CvFAxyc27GXpf02"
	onInputsAdded={(inputs) => {
		artist_ids = inputs;
	}}
	inputsTableName="sp_api_artist_ids"
/>

<!-- <form class="flex h-full w-full flex-col" method="POST" use:enhance onsubmit={handleSubmit}>
	{#if message !== null}
		{@const { type, text } = message}
		<MessageAlert {type} {text} />
	{/if}
	<Form.Field {form} name="artist_ids">
		<Form.Control>
			{#snippet children({ props })}
				
			{/snippet}
		</Form.Control>
		<Form.FieldErrors />
	</Form.Field>
	{#if $formData.artist_ids.length > 0}
		<div class="flex w-full justify-end">
			<Form.Button disabled={$formData.artist_ids.length == 0} class="mt-auto">
				Create Task
			</Form.Button>
		</div>
	{/if}
</form> -->
