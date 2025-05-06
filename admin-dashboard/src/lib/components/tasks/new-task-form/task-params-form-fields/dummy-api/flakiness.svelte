<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import type { FsSuperForm } from 'formsnap';
	import type { FlakyTaskParams } from '$lib/scraper-types-and-schemas/new-tasks/dummy-api';
	import Input from '$lib/components/ui/input/input.svelte';

	let { form }: { form: FsSuperForm<FlakyTaskParams> } = $props();
	let formData = form.form;
</script>

<Form.Field {form} name="flakiness">
	<Form.Control>
		{#snippet children({ props })}
			<Form.Label>Flakiness</Form.Label>
			<Input
				{...props}
				type="number"
				min="0"
				max="1"
				step="0.01"
				bind:value={$formData.flakiness}
			/>
		{/snippet}
	</Form.Control>
	<Form.Description>The probability of data fetching errors.</Form.Description>
	<Form.FieldErrors />
</Form.Field>
