<script lang="ts">
	import type { HTMLTableAttributes } from 'svelte/elements';
	import type { WithElementRef } from 'bits-ui';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		children,
		maxHeight,
		...restProps
	}: WithElementRef<HTMLTableAttributes> & { maxHeight: string } = $props();
</script>

<div class="relative w-full overflow-auto" style="max-height: {maxHeight}">
	<table bind:this={ref} class={cn('w-full caption-bottom text-sm', className)} {...restProps}>
		{@render children?.()}
	</table>
</div>
