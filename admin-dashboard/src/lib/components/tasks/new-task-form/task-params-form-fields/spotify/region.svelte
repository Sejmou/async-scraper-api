<script lang="ts">
	import * as Form from '$lib/components/ui/form';
	import * as Select from '$lib/components/ui/select';
	import type { FsSuperForm } from 'formsnap';
	import type { RegionParams } from '$lib/scraper-types-and-schemas/new-tasks/spotify-api';

	const regionOptions: { label: string; value: RegionParams['region'] }[] = [
		{ label: 'DE', value: 'de' },
		{ label: 'US', value: 'us' }
	];

	let { form }: { form: FsSuperForm<RegionParams> } = $props();
	let formData = form.form;
</script>

<Form.Field {form} name="region">
	<Form.Control>
		{#snippet children({ props })}
			<Form.Label>Region</Form.Label>
			<Select.Root {...props} bind:value={$formData.region} name={props.name} type="single">
				<Select.Trigger {...props} class="w-[180px]">
					{regionOptions.find((el) => el.value === $formData.region)?.label ?? 'Select a region'}
				</Select.Trigger>
				<Select.Content>
					{#each regionOptions as { label, value }}
						<Select.Item {label} value={value ?? ''} />
					{/each}
				</Select.Content>
			</Select.Root>
		{/snippet}
	</Form.Control>
	<Form.Description>The region for which data should be loaded.</Form.Description>
	<Form.FieldErrors />
</Form.Field>
