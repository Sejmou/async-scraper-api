import type { SpotifyAPITask } from '$lib/scraper-types-and-schemas/new-tasks/spotify-api';
import { sendTaskToScraper, type DataSourceTaskDispatchFn } from '.';

export const sendSpotifyApiTask: DataSourceTaskDispatchFn<SpotifyAPITask> = async (
	taskType,
	scraper,
	payload
) => {
	await sendTaskToScraper(scraper, {
		dataSource: 'spotify-api',
		taskType,
		payload
	});
};
