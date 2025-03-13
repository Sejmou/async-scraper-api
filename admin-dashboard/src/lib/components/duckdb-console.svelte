<script lang="ts">
	import { type DuckDB, type QueryOutputRowMajor } from '$lib/duckdb.svelte';
	import { truncate } from '$lib/utils';
	import { type Message, MessageAlert } from '$lib/components/ui/message-alert';
	import Textarea from './ui/textarea/textarea.svelte';

	let { duckDB }: { duckDB: DuckDB } = $props();
	let inputStr: string = $state('');
	let message: Message | null = $state(null);
	let result: QueryOutputRowMajor | null = $state(null);

	const processQueries = async (duckDB: DuckDB, raw_str: string) => {
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
				const out = await duckDB.executeQueryRowMajor(query);
				if (out.type === 'result') {
					console.log('got query result', result);
					result = out;
					message = null;
				}
				if (out.type === 'error') {
					result = null;
					message = {
						type: 'error',
						title: `Error executing query${queryCountStr}`,
						text: truncate(out.message, 512)
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
			processQueries(duckDB, inputStr);
		}
	}
</script>

{#if message !== null}
	{@const { type, title, text } = message}
	<MessageAlert {type} {title} {text} />
{/if}
<Textarea
	bind:value={inputStr}
	onkeydown={handleKeydown}
	placeholder="Enter SQL queries here..."
	rows={10}
	class="w-full"
/>
{#if result !== null}
	<pre>{JSON.stringify(result, null, 2)}</pre>
{/if}
