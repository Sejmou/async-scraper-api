import { dataSourceSchema, type DataSource } from '$lib/types-and-schemas/tasks/common.js';
import { error } from '@sveltejs/kit';

type PageData = {
	dataSource: {
		name: string;
		description: string;
	};
	taskCreatePages: {
		label: string;
		href: string;
	}[];
};

function getPageData(dataSource: DataSource): PageData {
	switch (dataSource) {
		case 'spotify-api':
			return {
				dataSource: {
					name: 'Spotify API',
					description: `Fetch data from Spotify's public API.`
				},
				taskCreatePages: [
					{
						label: 'Tracks',
						href: '/tasks/create/spotify-api/tracks'
					},
					{
						label: 'Albums',
						href: '/tasks/create/spotify-api/albums'
					},
					{
						label: 'Artists',
						href: '/tasks/create/spotify-api/artists'
					},
					{
						label: 'Artist Albums',
						href: '/tasks/create/spotify-api/artist-albums'
					},
					{
						label: 'Playlists',
						href: '/tasks/create/spotify-api/playlists'
					}
				]
			};
		case 'spotify-internal': {
			return {
				dataSource: {
					name: 'Internal (unofficial) Spotify APIs',
					description: `Fetch data from hidden APIs (normally only accessible to the Spotify webapp).`
				},
				taskCreatePages: [
					{
						label: 'Related Artists',
						href: '/tasks/create/spotify-internal/related-artists'
					}
				]
			};
		}
		case 'dummy-api':
			return {
				dataSource: {
					name: 'Dummy API',
					description: `Fetch data from a dummy API (useful for debugging of task execution logic without actually (ab-)using any real APIs).`
				},
				taskCreatePages: [
					{
						label: 'Flaky',
						href: '/tasks/create/dummy-api/flaky'
					},
					{
						label: 'Throw Above Threshold',
						href: '/tasks/create/dummy-api/throw-above-threshold'
					}
				]
			};
	}
}

export function load({ params }) {
	const dataSourceVal = params.dataSource;
	const parseRes = dataSourceSchema.safeParse(dataSourceVal);
	if (!parseRes.success) {
		return error(404, {
			message: 'Not found'
		});
	}

	return getPageData(parseRes.data);
}
