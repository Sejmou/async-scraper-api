<script lang="ts" generics="T extends z.ZodSchema">
	import { type DuckDBAPI, type QueryOutputRowMajor } from '$lib/duckdb.svelte';
	import { truncate } from '$lib/utils';
	import { type Message, ConsoleMessageAlert } from '$lib/components/ui/console-message-alert';
	import Textarea from '$lib/components/ui/textarea/textarea.svelte';
	import { z } from 'zod';
	import type { InputExtractorState } from '$lib/components/task-creator/input-extractor/index.svelte';
	import { Button } from '$lib/components/ui/button';
	// import ImportedInputsViewer from '../imported-inputs-viewer.svelte';
	import DuckDBQueryResultsTable from '$lib/components/duckdb-query-results-table.svelte';

	let { db, ieState }: { db: DuckDBAPI; ieState: InputExtractorState<T> } = $props();
	let { inputSchema } = ieState;

	let importSqlStr: string = $state('');
	let message: Message | null = $state(null);
	let result: QueryOutputRowMajor | null = $state(null);
	$inspect(result);

	const processQueries = async (db: DuckDBAPI, raw_str: string) => {
		try {
			if (!raw_str) {
				result = null;
				message = null;
				return;
			}
			const queries = raw_str.split(';').filter((str) => str.trim().length > 1);
			for (let i = 0; i < queries.length; i++) {
				const queryCountStr = queries.length > 1 ? ` (${i + 1}/${queries.length})` : '';
				const query = queries[i]!;
				message = {
					type: 'success',
					title: `Executing query${queryCountStr}`,
					text: truncate(query, 255)
				};
				const out = await db.executeQueryRowMajor(query);
				if (out.type === 'result') {
					// console.log('got query result', result);
					result = out;
					message = null;
				}
				if (out.type === 'error') {
					console.error(out.message);
					result = null;
					message = {
						type: 'error',
						title: `Error executing query${queryCountStr}`,
						text: out.message
					};
				}
			}
		} catch (e) {
			console.error(e);
			message = {
				type: 'error',
				title: 'Error processing queries',
				text: e instanceof Error ? e.message : String(e)
			};
			result = null;
		}
	};

	function handleKeydown(event: KeyboardEvent) {
		// Check if the user pressed "Enter"
		if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
			event.preventDefault(); // Prevent default behavior if necessary
			processQueries(db, importSqlStr);
		}
	}
</script>

{#if message !== null}
	{@const { type, title, text } = message}
	<ConsoleMessageAlert {type} {title} {text} />
{/if}
<Textarea
	bind:value={importSqlStr}
	onkeydown={handleKeydown}
	placeholder="Enter SQL quer(ies) for data import here..."
	rows={20}
/>
<div class="flex w-full justify-end">
	<Button>Run (Ctrl + Enter)</Button>
</div>
<h3 class="text-lg font-semibold">Results</h3>
{#if result !== null && result.type === 'result'}
	<DuckDBQueryResultsTable queryResults={result} />
{:else}
	<p class="text-sm">
		Adapt the SQL code above to produce the input values and run it. Results will be displayed here.
	</p>
{/if}
<!-- <ImportedInputsViewer {inputsValid} {ieState} /> -->
