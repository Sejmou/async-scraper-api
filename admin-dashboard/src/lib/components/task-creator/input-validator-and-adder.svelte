<script lang="ts" generics="T extends z.ZodSchema">
	import { z } from 'zod';
	import type { InputExtractorState } from './input-extractor/index.svelte';
	import type { DuckDBAPI } from '$lib/duckdb.svelte';
	import { Button } from '../ui/button';
	import * as Alert from '$lib/components/ui/alert';
	import CircleAlert from 'lucide-svelte/icons/circle-alert';
	import type { Message } from '../ui/console-message-alert';

	let { ieState, db }: { ieState: InputExtractorState<T>; db: DuckDBAPI } = $props();

	let validating = $state(false);
	let message: Message | null = $state(null);

	let validateAndAddInputs = async () => {
		if (validating) return;
		validating = true;
		const out = await db.executeQueryColMajor(`SELECT * FROM ${ieState.inputsTableName}`);
		if (out.type === 'error') {
			message = {
				type: 'error',
				title: 'Error validating inputs',
				text: out.error?.message || 'Unknown error (check the console)'
			};
			return;
		}
		const columns = out.columns;
		if (columns.length !== 1) {
			message = {
				type: 'error',
				title: 'Error validating inputs',
				text: `Expected 1 column of data, but got ${columns.length}`
			};
			return;
		}
		const nonValidatedData = out.data[out.columns[0]];
		try {
			const data = z.array(ieState.inputSchema).parse(nonValidatedData);
			ieState.inputs = data;
			message = {
				type: 'success',
				title: 'Inputs validated',
				text: `${data.length} inputs have been successfully validated and added to the task :)`
			};
		} catch (e) {
			message = {
				type: 'error',
				title: 'Error validating inputs',
				text: e instanceof Error ? e.message : 'Unknown error (check the console)'
			};
		}
		validating = false;
	};
</script>

<h3 class="text-lg font-semibold">Add extracted inputs to task</h3>
{#if message}
	<Alert.Root variant={message.type === 'error' ? 'destructive' : 'default'}>
		<CircleAlert class="size-4" />
		<Alert.Title>
			{#if message.title}
				{message.title}
			{:else}
				Error
			{/if}
		</Alert.Title>
		<Alert.Description>{message.text}</Alert.Description>
	</Alert.Root>
{/if}
<p class="text-sm">
	{#if ieState.inputsTableHasData}
		You have successfully extracted data. If you're confident the inputs are what you need (and is
		expected for this task), click the button below to add it to the task (it will be validated
		against the expected schema).
	{:else}
		Once you've run your SQL for data extraction, you'll be able to add your extracted inputs to the
		task. They will have to match the expected schema (as shown in the example above).
	{/if}
</p>
<Button disabled={validating || !ieState.inputsTableHasData} onclick={validateAndAddInputs}>
	{#if ieState.inputs.length === 0}
		Add Data to Task
	{:else}
		Update Task Data
	{/if}
</Button>
