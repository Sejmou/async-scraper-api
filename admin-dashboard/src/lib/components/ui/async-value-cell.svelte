<script lang="ts" generics="T extends Promise<any>">
	type Props<T> = {
		valuePromise: T;
		accessorFn: (value: Awaited<T>) => any;
	};

	let { valuePromise, accessorFn }: Props<T> = $props();
</script>

{#await valuePromise}
	<div>Loading...</div>
{:then value}
	<span>{accessorFn(value)}</span>
{:catch error}
	<span>Error: {error.message}</span>
{/await}
