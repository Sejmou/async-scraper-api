<script lang="ts">
	import { type DuckDBAPI, type QueryExecutionError } from '$lib/duckdb.svelte';
	import { truncate } from '$lib/utils';
	import { type Message, ConsoleMessageAlert } from '$lib/components/ui/console-message-alert';
	import Textarea from '$lib/components/ui/textarea/textarea.svelte';
	import { Button } from '$lib/components/ui/button';
	import DuckDBTableViewer from '$lib/components/duckdb/duckdb-table-viewer.svelte';

	let { db }: { db: DuckDBAPI } = $props();

	let importSqlStr: string = $state('');
	let message: Message | null = $state(null);
	const resultsTableName = 'tmp_query_results';
	let resultsComputed = $state(false);

	const processQueries = async (db: DuckDBAPI, raw_str: string) => {
		resultsComputed = false;
		if (!raw_str) {
			message = null;
			return;
		}

		try {
			await db.executeQueryRowMajor(`DROP TABLE IF EXISTS ${resultsTableName}`);

			const queries = raw_str.split(';').filter((str) => str.trim().length > 1);

			const handleQueryError: (queryCountStr: string, error: QueryExecutionError) => void = (
				queryCountStr,
				error
			) => {
				const msg = error.message;
				console.error(msg);
				resultsComputed = false;
				message = {
					type: 'error',
					title: `Error executing query${queryCountStr}`,
					text: msg
				};
			};

			for (let i = 0; i < queries.length; i++) {
				const queryCountStr = queries.length > 1 ? ` (${i + 1}/${queries.length})` : '';
				const query = queries[i]!;
				message = {
					type: 'success',
					title: `Executing query${queryCountStr}`,
					text: truncate(query, 255)
				};

				const isLastQuery = i === queries.length - 1;
				if (!isLastQuery) {
					const out = await db.executeQueryRowMajor(query);
					// only care about result of last query!
					if (out.type === 'error') {
						handleQueryError(queryCountStr, out);
						return;
					}
				} else {
					const out = await db.executeQueryRowMajor(`CREATE TABLE ${resultsTableName} AS ${query}`);
					if (out.type === 'result') {
						resultsComputed = true;
						message = null;
					} else {
						handleQueryError(queryCountStr, out);
						return;
					}
				}
			}
		} catch (e) {
			console.error(e);
			message = {
				type: 'error',
				title: 'Error processing queries',
				text: e instanceof Error ? e.message : String(e)
			};
			resultsComputed = false;
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
{#if resultsComputed}
	<DuckDBTableViewer tableName={resultsTableName} {db} />
{:else}
	<p class="text-sm">Results will be displayed here.</p>
{/if}
<!-- <ImportedInputsViewer {inputsValid} {ieState} /> -->
