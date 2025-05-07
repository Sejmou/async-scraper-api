<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import { MessageAlert } from '$lib/components/ui/message-alert';
	import { InputExtractor } from '$lib/components/tasks/task-input-extractor/index.svelte';
	import SpotifyRegionParamFormField from './task-params-form-fields/spotify/region.svelte';
	import SpotifyArtistAlbumsReleaseTypesFormFields from './task-params-form-fields/spotify/artist-albums-release-types.svelte';

	import { getTaskFormState } from './index.svelte';
	import ScraperTable from './scraper-table.svelte';
	import DummyApiTaskFlakiness from './task-params-form-fields/dummy-api/flakiness.svelte';
	import DummyApiTaskThrowThreshold from './task-params-form-fields/dummy-api/threshold.svelte';

	const state = getTaskFormState();

	let { exampleInput, inputsDescription, inputSchema, inputsTableName } = $derived(state.inputMeta);
	let message = state.message;
	let inputs = $derived(state.inputs);
	let initialTaskValue = $derived(state.initialTaskValue);
	let form = $derived(state.form);
	let availableScrapers = $derived(state.availableScrapers);
	let selectedScraperIds = $derived(state.selectedScraperIds);
</script>

<form method="POST" use:state.enhance onsubmit={(e) => state.handleSubmit(e)}>
	{#if $message !== undefined}
		{@const { type, text } = $message}
		<MessageAlert
			class="mb-4"
			title={$message.type === 'error' ? 'Task creation failed' : undefined}
			{type}
			{text}
		/>
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
			{:else if initialTaskValue.dataSource === 'dummy-api'}
				{#if 'params' in initialTaskValue}
					{@const params = initialTaskValue.params}
					{#if 'flakiness' in params}
						<DummyApiTaskFlakiness {form} />
					{/if}
					{#if 'threshold' in params}
						<DummyApiTaskThrowThreshold {form} />
					{/if}
				{/if}
			{/if}
		</div>
	{/if}
	<h3 class="mt-4 text-lg font-semibold">Scrapers</h3>
	{#if availableScrapers.length === 0}
		<p class="text-sm text-muted-foreground">
			No scrapers available at this time. Unfortunately, this means you can't create the task :/
		</p>
	{:else}
		<ScraperTable />
		<div class="my-2 text-sm text-muted-foreground">
			{#if selectedScraperIds.length === 0}
				Select at least one scraper to run this task on. The inputs will be distributed evenly among
				them.
			{:else}
				{selectedScraperIds.length} scraper{selectedScraperIds.length > 1 ? 's' : ''} selected.
				{#if selectedScraperIds.length === 1}
					It will process all {inputs.length > 0 ? inputs.length + ' ' : ''}inputs.
				{:else}
					The {inputs.length > 0 ? inputs.length + ' ' : ''}inputs will be distributed evenly among
					them.
				{/if}
				{#if inputs.length > 0 && selectedScraperIds.length > 1}
					{@const inputsPerScraper = inputs.length / selectedScraperIds.length}
					{@const integerResult = inputsPerScraper % 1 === 0}
					Each scraper will process {!integerResult ? 'around' : ''}
					{Math.round(inputs.length / selectedScraperIds.length)} inputs.
				{/if}
			{/if}
		</div>
	{/if}
	<div class="mt-4 flex w-full justify-end">
		<Form.Button
			disabled={availableScrapers.length === 0 ||
				inputs.length === 0 ||
				selectedScraperIds.length === 0}
			type="submit">Create task</Form.Button
		>
	</div>
</form>
