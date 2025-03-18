import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [sveltekit()],

	build: {
		target: 'ES2022'
	},

	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	}
});
