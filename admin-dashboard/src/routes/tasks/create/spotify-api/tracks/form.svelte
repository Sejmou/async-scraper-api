<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import { type TracksParamsSchema } from '$lib/scraper-types-and-schemas/new-tasks/spotify-api';
	import { type SuperValidated, type Infer, superForm } from 'sveltekit-superforms';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import { InputExtractor } from '$lib/components/task-input-extractor/index.svelte';
	import * as Select from '$lib/components/ui/select';
	import { z } from 'zod';

	let { tracksForm }: { tracksForm: SuperValidated<Infer<TracksParamsSchema>> } = $props();

	const form = superForm(tracksForm, {
		dataType: 'json'
	});

	const { form: formData, enhance } = form;

	const regionOptions: { label: string; value: z.infer<TracksParamsSchema>['region'] }[] = [
		{ label: 'DE', value: 'de' },
		{ label: 'US', value: 'us' }
	];

	let trackIds: string[] = $state([]);
	let formMessage = form.message;
</script>

<form method="POST" use:enhance>
	{#if $formMessage !== undefined}
		{@const { type, text } = $formMessage}
		<MessageAlert {type} {text} />
	{/if}
	<h3 class="text-lg font-semibold">Inputs (Track IDs)</h3>
	<InputExtractor
		inputDescription="Track IDs"
		exampleInput="4PTG3Z6ehGkBFwjybzWkR8"
		inputSchema={z.string()}
		onInputsAdded={(inputs) => (trackIds = inputs)}
		inputsTableName="sp_api_track_ids"
	/>
	{#if trackIds.length > 0}
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
