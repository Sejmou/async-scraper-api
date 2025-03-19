<script lang="ts">
	import {
		type SupportedTask,
		type SupportedTaskInputMeta
	} from '$lib/scraper-types-and-schemas/new-tasks';
	import * as Form from '$lib/components/ui/form';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import { InputExtractor } from '$lib/components/task-input-extractor/index.svelte';
	import { z } from 'zod';
	import { TaskFormState } from './index.svelte';

	import SpotifyTracksParamsFormFields from './task-params-form-fields/spotify/tracks.svelte';

	let {
		initialTaskValue,
		taskInputMeta,
		paramsSchema = z.object({
			// Default schema for tasks that don't have any parameters
		})
	}: {
		initialTaskValue: SupportedTask;
		paramsSchema?: z.ZodSchema;
		taskInputMeta: SupportedTaskInputMeta;
	} = $props();
	let { form, message, handleSubmit, enhance, inputs, updateInputs } = $derived(
		new TaskFormState(initialTaskValue, paramsSchema)
	);

	let { exampleInput, inputDescription, inputSchema, inputsTableName } = $derived(taskInputMeta);
</script>

<form method="POST" use:enhance onsubmit={handleSubmit}>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert {type} {text} />
	{/if}
	<h3 class="text-lg font-semibold">Inputs (Track IDs)</h3>
	<InputExtractor
		{inputDescription}
		{exampleInput}
		{inputSchema}
		{inputsTableName}
		onInputsAdded={(newInputs) => updateInputs(newInputs)}
	/>
	{#if inputs.length > 0}
		{#if 'params' in initialTaskValue}
			<h3 class="mt-4 text-lg font-semibold">Parameters</h3>
			{#if initialTaskValue.dataSource === 'spotify-api'}
				{#if initialTaskValue.taskType === 'tracks'}
					<SpotifyTracksParamsFormFields {form} />
				{/if}
			{/if}
		{/if}
		<div class="mt-4 flex w-full justify-end">
			<Form.Button type="submit">Create task</Form.Button>
		</div>
	{/if}
</form>
