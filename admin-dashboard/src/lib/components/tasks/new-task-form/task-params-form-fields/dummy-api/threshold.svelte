<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import type { FsSuperForm } from 'formsnap';
	import type { ThrowAboveThresholdTaskParams } from '$lib/scraper-types-and-schemas/new-tasks/dummy-api';
	import Input from '$lib/components/ui/input/input.svelte';

	let { form }: { form: FsSuperForm<ThrowAboveThresholdTaskParams> } = $props();
	let formData = form.form;
</script>

<Form.Field {form} name="threshold">
	<Form.Control>
		{#snippet children({ props })}
			<Form.Label>ID Threshold</Form.Label>
			<Input {...props} type="number" min="0" step="1" bind:value={$formData.threshold} />
		{/snippet}
	</Form.Control>
	<Form.Description>The biggest ID (integer) for which no error is thrown (lol)</Form.Description>
	<Form.FieldErrors />
</Form.Field>
