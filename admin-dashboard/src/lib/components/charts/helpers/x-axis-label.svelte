<script>
	let {
		width,
		height,
		margin,
		label,
		xoffset = 0,
		yoffset = 0,
		position = 'center', // 'left', 'center', 'right'
		textanchor = 'middle', // Default anchor for centered text
		fillColor = 'white'
	} = $props();

	// Calculate x position for the label
	const calculateXPosition = () => {
		if (position === 'left') return margin.left + xoffset;
		if (position === 'right') return margin.left + width + xoffset;
		return width / 2 - margin.left / 2 + xoffset; // Default: center
	};
</script>

<text
	fill={fillColor}
	x={calculateXPosition()}
	y={height - margin.bottom + 40 + yoffset}
	text-anchor={textanchor}
>
	{label}
</text>
