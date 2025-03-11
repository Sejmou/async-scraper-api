import Root from './message-alert.svelte';

type Message = {
	type: 'error' | 'success';
	text: string;
};

export { Root, type Message, Root as MessageAlert };
