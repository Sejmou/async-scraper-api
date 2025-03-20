<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import { InputExtractor } from '$lib/components/task-input-extractor/index.svelte';
	import SpotifyRegionParamFormField from './task-params-form-fields/spotify/region.svelte';
	import SpotifyArtistAlbumsReleaseTypesFormFields from './task-params-form-fields/spotify/artist-albums-release-types.svelte';

	import { getTaskFormState } from './index.svelte';

	const state = getTaskFormState();

	let { exampleInput, inputsDescription, inputSchema, inputsTableName } = $derived(state.inputMeta);
	let message = $derived(state.message);
	let inputs = $derived(state.inputs);
	let initialTaskValue = $derived(state.initialTaskValue);
	let form = $derived(state.form);
</script>

<form method="POST" use:state.enhance onsubmit={(e) => state.handleSubmit(e)}>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert {type} {text} />
	{/if}
	<h3 class="text-lg font-semibold">Inputs ({inputsDescription})</h3>
	<InputExtractor
		{inputsDescription}
		{exampleInput}
		{inputSchema}
		{inputsTableName}
		onInputsAdded={(newInputs) => state.updateInputs(newInputs)}
	/>
	{#if 'params' in initialTaskValue}
		<h3 class="mt-4 text-lg font-semibold">Parameters</h3>
		<div class="flex flex-col gap-4">
			{#if initialTaskValue.dataSource === 'spotify-api'}
				{#if 'params' in initialTaskValue}
					{@const params = initialTaskValue.params}
					{#if 'region' in params}
						<SpotifyRegionParamFormField {form} />
					{/if}
					{#if 'release_types' in params}
						<SpotifyArtistAlbumsReleaseTypesFormFields {form} />
					{/if}
				{/if}
			{/if}
		</div>
	{/if}
	<div class="mt-4 flex w-full justify-end">
		<Form.Button disabled={inputs.length == 0} type="submit">Create task</Form.Button>
	</div>
</form>
