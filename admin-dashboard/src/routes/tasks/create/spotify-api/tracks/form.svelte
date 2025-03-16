<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import {
		tracksParamsSchema,
		type SpotifyAPITask,
		type TracksParamsSchema
	} from '$lib/scraper-types-and-schemas/new-tasks/spotify-api';
	import { superForm, defaults } from 'sveltekit-superforms';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import { InputExtractor } from '$lib/components/task-input-extractor/index.svelte';
	import * as Select from '$lib/components/ui/select';
	import { z } from 'zod';
	import { zod } from 'sveltekit-superforms/adapters';
	import { createTask } from '$lib/client-api/scraper-tasks';
	import { goto } from '$app/navigation';

	// NOTE: it would have been nice to use form actions with validation by SvelteKit Superforms
	// However, I couldn't make it work with large payloads (e.g. for track IDs) - the UI freezes
	// I don't exactly understand the issue, but it has something to do with state tracking issues for huge arrays
	const form = superForm(defaults(zod(tracksParamsSchema)), {
		SPA: true,
		validators: zod(tracksParamsSchema),
		resetForm: false
	});

	const regionOptions: { label: string; value: z.infer<TracksParamsSchema>['region'] }[] = [
		{ label: 'DE', value: 'de' },
		{ label: 'US', value: 'us' }
	];

	const { form: formData, enhance, validateForm, errors } = form;

	let track_ids: string[] = $state([]);

	async function handleSubmit(event: Event) {
		event.preventDefault();
		const result = await validateForm();

		if (!result.valid) {
			errors.update((v) => {
				return {
					...v,
					region: result.errors.region
				};
			});
			return;
		}

		const task: SpotifyAPITask = {
			dataSource: 'spotify-api',
			taskType: 'tracks',
			payload: {
				track_ids,
				region: $formData.region
			}
		};

		const { id } = await createTask(task);
		await goto(`/tasks/${id}`);
	}

	let formMessage = form.message;
</script>

<form method="POST" use:enhance onsubmit={handleSubmit}>
	{#if $formMessage !== undefined}
		{@const { type, text } = $formMessage}
		<MessageAlert {type} {text} />
	{/if}
	<h3 class="text-lg font-semibold">Inputs (Track IDs)</h3>
	<InputExtractor
		inputDescription="Track IDs"
		exampleInput="4PTG3Z6ehGkBFwjybzWkR8"
		inputSchema={z.string()}
		inputsTableName="sp_api_track_ids"
		onInputsAdded={(inputs) => (track_ids = inputs)}
	/>
	{#if track_ids.length > 0}
		<h3 class="mt-4 text-lg font-semibold">Parameters</h3>
		<Form.Field {form} name="region">
			<Form.Control>
				{#snippet children({ props })}
					<Form.Label>Region</Form.Label>
					<Select.Root {...props} bind:value={$formData.region} name={props.name} type="single">
						<Select.Trigger {...props} class="w-[180px]">
							{regionOptions.find((el) => el.value === $formData.region)?.label ??
								'Select a region'}
						</Select.Trigger>
						<Select.Content>
							{#each regionOptions as { label, value }}
								<Select.Item {label} value={value ?? ''} />
							{/each}
						</Select.Content>
					</Select.Root>
				{/snippet}
			</Form.Control>
			<Form.Description>The region for which metadata should be loaded.</Form.Description>
			<Form.FieldErrors />
		</Form.Field>
		<div class="mt-4 flex w-full justify-end">
			<Form.Button type="submit">Create task</Form.Button>
		</div>
	{/if}
</form>
