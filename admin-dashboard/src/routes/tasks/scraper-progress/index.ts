import type { ScraperSubtaskProgress } from '$lib/server/scraper-api/subtask-progress';

export type ScraperProgressData = Promise<ScraperSubtaskProgress | null>;
