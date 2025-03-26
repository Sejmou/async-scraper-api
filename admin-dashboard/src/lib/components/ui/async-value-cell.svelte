<script lang="ts" generics="T">
	type Props<T> = {
		valuePromise: Promise<T>;
		accessorFn: (value: T) => any;
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
