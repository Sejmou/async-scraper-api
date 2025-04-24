<script lang="ts">
	import type { ScaleLinear } from 'd3-scale';

	let {
		yScale,
		margin,
		ticksNumber = 5
	}: {
		yScale: ScaleLinear<number, number>;
		margin: { top: number; right: number; bottom: number; left: number };
		ticksNumber?: number;
	} = $props();
</script>

{#if yScale}
	<g transform="translate({margin.left},0)">
		<!-- yScale.domain() is an array with two elements min and max values 
    from the data, so we can use it to create the start and end point
    of our axis line -->
		<line stroke="currentColor" y1={yScale(0)} y2={yScale(yScale.domain()[1])} />
		<!-- Specify the number of ticks here -->
		{#each yScale.ticks(ticksNumber) as tick}
			{#if tick !== 0}
				<line stroke="currentColor" x1={0} x2={-6} y1={yScale(tick)} y2={yScale(tick)} />
			{/if}

			<text
				fill="currentColor"
				text-anchor="end"
				font-size="10"
				dominant-baseline="middle"
				x={-9}
				y={yScale(tick)}
			>
				{tick}
			</text>
		{/each}
	</g>
{/if}
