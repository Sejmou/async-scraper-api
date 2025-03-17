<script lang="ts">
	// This component is a stupid workaround to allow me to create a button with text from renderComponent in a DataTable cell
	// TODO: figure out how to pass children to renderComponent directly (couldn't figure it out yet)
	import Button from './button/button.svelte';
	import { type ButtonProps } from './button';

	let { text, ...rest }: ButtonProps & { text: string } = $props();
</script>

<Button {...rest}>{text}</Button>
