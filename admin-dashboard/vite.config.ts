import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [sveltekit()],

	build: {
		target: 'ES2022'
	},

	ssr: {
		noExternal: ['monaco-editor'] // to completely exclude Monaco in SSR
	},

	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	},

	server: {
		allowedHosts: ["dev.sejmou.xyz"]
	}
});
