import { defineConfig } from '@playwright/test';

export default defineConfig({
	webServer: {
		command: 'npm run build && npm run preview',
		port: 4173,
		// build takes more than default 120s
		timeout: 180 * 1000
	},

	testDir: 'e2e'
});
