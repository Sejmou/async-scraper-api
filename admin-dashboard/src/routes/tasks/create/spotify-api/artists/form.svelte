<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import {
		artistsPayloadSchema,
		type SpotifyAPITask
	} from '$lib/scraper-types-and-schemas/new-tasks/spotify-api';
	import { superForm, defaults } from 'sveltekit-superforms';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import { InputExtractor } from '$lib/components/task-input-extractor/index.svelte';
	import { z } from 'zod';
	import { zod } from 'sveltekit-superforms/adapters';
	import { createTask } from '$lib/client-api/scraper-tasks';
	import { goto } from '$app/navigation';

	// NOTE: we don't utilize the artists schema at all, validation happens inside the InputExtractor component
	// we just need to pass _something_ so that superforms is happy - this is hacky af, I know lol
	const form = superForm(defaults(zod(artistsPayloadSchema)), {
		SPA: true,
		dataType: 'json',
		validators: zod(artistsPayloadSchema),
		resetForm: false
	});

	const { form: formData, enhance, validateForm, errors } = form;

	let artist_ids: string[] = $state([]);

	async function handleSubmit(event: Event) {
		console.log('artist_ids', artist_ids);
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

		const task: SpotifyAPITask = {
			dataSource: 'spotify-api',
			taskType: 'artists',
			payload: {
				artist_ids
			}
		};

		console.log('task', task);
		const res = await createTask(task);
		console.log('res', res);
		if (res.status === 'success') {
			await goto(`/tasks/${res.id}`);
		} else {
			formMessage.set({
				type: 'error',
				text: res.error
			});
		}
	}

	let formMessage = form.message;
</script>

<form method="POST" use:enhance onsubmit={handleSubmit}>
	{#if $formMessage !== undefined}
		{@const { type, text } = $formMessage}
		<MessageAlert {type} {text} />
	{/if}
	<h3 class="text-lg font-semibold">Inputs (artist IDs)</h3>
	<InputExtractor
		inputDescription="artist IDs"
		exampleInput="4PTG3Z6ehGkBFwjybzWkR8"
		inputSchema={z.string()}
		inputsTableName="sp_api_artist_ids"
		onInputsAdded={(inputs) => (artist_ids = inputs)}
	/>
	{#if artist_ids.length > 0}
		<div class="mt-4 flex w-full justify-end">
			<Form.Button type="submit">Create task</Form.Button>
		</div>
	{/if}
</form>
