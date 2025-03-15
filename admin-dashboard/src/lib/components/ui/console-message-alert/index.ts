import Root from './message-alert.svelte';

type Message = {
	type: 'error' | 'success';
	title?: string;
	text: string;
};

export { Root, type Message, Root as ConsoleMessageAlert };
