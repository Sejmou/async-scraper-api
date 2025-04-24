<script>
	let {
		height,
		margin,
		label,
		xoffset = 0,
		yoffset = 0,
		position = 'center', // 'top', 'center', 'bottom'
		textanchor = 'end', // Default anchor for vertical text
		fillColor = 'white'
	} = $props();

	// Calculate y position for the label
	const calculateYPosition = () => {
		if (position === 'top') return -margin.top + 40 + yoffset;
		if (position === 'bottom') return height + margin.top + 40 + yoffset;
		return height / 2 + margin.top / 2 + 40 + yoffset; // Default: center
	};
</script>

<text fill={fillColor} x={margin.left + xoffset} y={calculateYPosition()} text-anchor={textanchor}>
	{label}
</text>
