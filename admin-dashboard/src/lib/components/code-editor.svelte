<script lang="ts">
	// built on top of awesome 'template' by ala-garbaa-pro on GitHub: https://github.com/ala-garbaa-pro/svelte-5-monaco-editor-two-way-binding?tab=readme-ov-file#codeeditor-component
	import { cn } from '$lib/utils';
	import loader from '@monaco-editor/loader';
	import type * as Monaco from 'monaco-editor/esm/vs/editor/editor.api';
	import { onDestroy, onMount } from 'svelte';

	let editor: Monaco.editor.IStandaloneCodeEditor;
	let monaco: typeof Monaco;
	let editorContainer: HTMLElement;

	type Props = {
		value: string;
		language?: string;
		theme?: string;
		class?: string;
		minimap?: boolean;
		keybindings?: {
			keybinding: number;
			handler: Monaco.editor.ICommandHandler;
		}[];
		readOnly?: boolean;
		scrollbarAlwaysConsumeMouseWheel?: boolean;
	};

	let {
		value = $bindable(),
		class: className = '',
		language = 'sql',
		theme = 'quietlight',
		minimap = false,
		keybindings = [],
		readOnly = false,
		scrollbarAlwaysConsumeMouseWheel = false
	}: Props = $props();

	onMount(() => {
		(async () => {
			const monacoEditor = await import('monaco-editor');
			loader.config({ monaco: monacoEditor.default });

			monaco = await loader.init();

			editor = monaco.editor.create(editorContainer, {
				value,
				language,
				theme,
				readOnly,
				minimap: {
					enabled: minimap
				},
				automaticLayout: true,
				scrollbar: {
					alwaysConsumeMouseWheel: scrollbarAlwaysConsumeMouseWheel
				},
				overviewRulerLanes: 0,
				overviewRulerBorder: false,
				wordWrap: 'on'
			});

			editor.onDidChangeModelContent((e) => {
				if (e.isFlush) {
					// true if setValue call
					//console.log('setValue call');
					/* editor.setValue(value); */
				} else {
					// console.log('user input');
					const updatedValue = editor?.getValue() ?? ' ';
					value = updatedValue;
				}
			});

			editor.addCommand(monaco.KeyCode.Escape, () => {
				if (!(document.activeElement instanceof HTMLTextAreaElement)) {
					console.warn(
						'Escape key pressed in editor, but not in textarea!? This should not happen'
					);
					return;
				}
				document.activeElement?.blur();
			});

			for (const { keybinding, handler } of keybindings) {
				editor.addCommand(keybinding, handler);
			}
		})();
	});

	$effect(() => {
		if (value) {
			if (editor) {
				// check if the editor is focused
				if (editor.hasWidgetFocus()) {
					// let the user edit with no interference
				} else {
					if (editor?.getValue() ?? ' ' !== value) {
						editor?.setValue(value);
					}
				}
			}
		}
		if (value === '') {
			editor?.setValue(' ');
		}
	});

	onDestroy(() => {
		monaco?.editor.getModels().forEach((model) => model.dispose());
		editor?.dispose();
	});
</script>

<div
	class={cn('rounded-lg border  py-4 pr-4 focus-within:border-muted-foreground', className)}
	role="textbox"
	tabindex="0"
	bind:this={editorContainer}
></div>
