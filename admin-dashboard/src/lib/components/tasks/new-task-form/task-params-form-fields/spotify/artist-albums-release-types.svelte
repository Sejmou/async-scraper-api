<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import type { FsSuperForm } from 'formsnap';
	import type { ArtistAlbumsParamsReleaseTypes } from '$lib/scraper-types-and-schemas/new-tasks/spotify-api';

	let { form }: { form: FsSuperForm<ArtistAlbumsParamsReleaseTypes> } = $props();
	let formData = form.form;

	type ReleaseType = keyof ArtistAlbumsParamsReleaseTypes['release_types'];

	const releaseTypes = Object.keys($formData.release_types) as ReleaseType[];
	type ReleaseTypeLabelMapping = {
		[K in keyof ArtistAlbumsParamsReleaseTypes['release_types']]: string;
	};
	const labels: ReleaseTypeLabelMapping = {
		albums: 'Albums',
		singles: 'Singles',
		compilations: 'Compilations',
		appears_on: 'Appears On'
	};
	function setReleaseType(type: ReleaseType, value: boolean) {
		$formData.release_types[type] = value;
	}
</script>

<Form.Fieldset {form} name="release_types">
	<div class="mb-2">
		<Form.Legend>Release Types</Form.Legend>
		<Form.Description>The types of releases to load for each artist.</Form.Description>
	</div>
	<div class="space-y-2">
		{#each releaseTypes as type}
			{@const checked = $formData.release_types[type]}
			<div class="flex flex-row items-start space-x-3">
				<Form.Control>
					{#snippet children({ props })}
						<Checkbox
							{...props}
							{checked}
							value={type}
							onCheckedChange={(v) => {
								setReleaseType(type, v);
							}}
						/>
						<Form.Label class="font-normal">
							{labels[type]}
						</Form.Label>
					{/snippet}
				</Form.Control>
			</div>
		{/each}
		<Form.FieldErrors />
	</div>
</Form.Fieldset>
