<script lang="ts">
	import {
		type DuckDBAPI,
		type QueryExecutionError,
		type QueryOutputRowMajor
	} from '$lib/duckdb.svelte';
	import { truncate } from '$lib/utils';
	import { type Message, ConsoleMessageAlert } from '$lib/components/ui/console-message-alert';
	import CodeEditor from '$lib/components/code-editor.svelte';
	import { Button } from '$lib/components/ui/button';
	import DuckDBTableViewer from './duckdb-table-viewer.svelte';
	import { KeyCode, KeyMod } from 'monaco-editor';

	let {
		db,
		resultsTableName = 'tmp_query_results',
		onOutput = () => {},
		onError = () => {}
	}: {
		db: DuckDBAPI;
		resultsTableName?: string;
		onOutput?: (output: QueryOutputRowMajor) => void;
		onError?: (error: QueryExecutionError) => void;
	} = $props();

	let importSqlStr: string = $state('');
	let message: Message | null = $state(null);
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
				onError(error);
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
						onOutput(out);
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
</script>

{#if message !== null}
	{@const { type, title, text } = message}
	<ConsoleMessageAlert {type} {title} {text} />
{/if}
<CodeEditor
	bind:value={importSqlStr}
	language="sql"
	class="min-h-[600px]"
	keybindings={[
		{
			keybinding: KeyMod.CtrlCmd | KeyCode.Enter,
			handler: () => {
				processQueries(db, importSqlStr);
			}
		}
	]}
/>
<div class="flex w-full justify-end">
	<Button onclick={() => processQueries(db, importSqlStr)}>Run (Ctrl/Cmd + Enter)</Button>
</div>
<div class="w-full">
	<h3 class="font-semibold">Results</h3>
	{#if resultsComputed}
		<DuckDBTableViewer tableName={resultsTableName} {db} />
	{:else}
		<p class="text-sm text-muted-foreground">Results will be displayed here.</p>
	{/if}
</div>
