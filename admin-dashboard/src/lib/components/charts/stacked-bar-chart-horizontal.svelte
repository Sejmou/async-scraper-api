<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import { cumsum, sum } from 'd3-array';
	import * as Popover from '$lib/components/ui/popover';

	type Props = {
		data: {
			label: string;
			value: number;
			color: string;
		}[];
		dataDescSingular: string;
		dataDescPlural: string;
		barWidth?: number;
	};

	let { data, dataDescSingular, dataDescPlural, barWidth = 100 }: Props = $props();
	const height = 15;
	let total = $derived(sum(data, (d) => d.value));

	let scaleX = $derived(scaleLinear().domain([0, total]).range([0, barWidth]));

	let cumSumData = $derived(cumsum(data, (d) => d.value));
</script>

<Popover.Root>
	<Popover.Trigger>
		<div class="flex items-center gap-2 px-4 py-2">
			<div style="width: {barWidth}px" class="w-full rounded-xl">
				<svg
					width="100%"
					viewBox={`0 0 ${barWidth} ${height}`}
					{height}
					xmlns="http://www.w3.org/2000/svg"
					font-family="sans-serif"
				>
					{#each data as { value, color }, i}
						<rect
							x={scaleX(cumSumData[i] - value)}
							y="0"
							width={scaleX(value)}
							{height}
							fill={color}
						/>
					{/each}
				</svg>
			</div>
			<span class="text-nowrap text-sm text-muted-foreground">
				{total}
				{total === 1 ? dataDescSingular : dataDescPlural}
			</span>
		</div>
	</Popover.Trigger>
	<Popover.Content class="w-full">
		<div class="flex flex-col gap-2">
			{#each data as { label, value, color }}
				<div class="flex items-center gap-2">
					<div class="h-3 w-3 rounded-full" style="background-color: {color};"></div>
					<span class="text-sm text-muted-foreground">{label}: {value}</span>
				</div>
			{/each}
		</div>
	</Popover.Content>
</Popover.Root>
