import {
	getInitialTaskValue,
	getParamsSchema,
	type SupportedTask,
	type SupportedTaskInputMeta
} from '$lib/scraper-types-and-schemas/new-tasks';
import { error } from '@sveltejs/kit';
import { z } from 'zod';

export function load({ params }) {
	const dataSource = 'spotify-api';
	const { taskType } = params;

	const initialTaskValue = getInitialTaskValue(dataSource, taskType);
	if (!initialTaskValue) {
		return error(404, {
			message: 'Not found'
		});
	}

	const paramsSchema = getParamsSchema(initialTaskValue);
	const taskInputMeta = getTaskInputMeta(initialTaskValue);

	console.log({ initialTaskValue, paramsSchema, taskInputMeta });

	return {
		dataSource,
		taskType,
		initialTaskValue,
		paramsSchema: paramsSchema || undefined,
		taskInputMeta
	};
}

function getTaskInputMeta(task: SupportedTask): SupportedTaskInputMeta {
	// TODO: update as more data sources and task types are added
	switch (task.dataSource) {
		case 'spotify-api':
			switch (task.taskType) {
				case 'artists':
					return {
						exampleInput: '06HL4z0CvFAxyc27GXpf02',
						inputDescription: 'Spotify artist ID',
						inputSchema: z.string(),
						inputsTableName: 'sp_api_artists'
					};
				case 'tracks':
					return {
						exampleInput: '4PTG3Z6ehGkBFwjybzWkR8',
						inputDescription: 'Spotify track ID',
						inputSchema: z.string(),
						inputsTableName: 'sp_api_tracks'
					};
				case 'artist-albums':
					return {
						exampleInput: '4PTG3Z6ehGkBFwjybzWkR8',
						inputDescription: 'Spotify artist ID',
						inputSchema: z.string(),
						inputsTableName: 'sp_api_artist_albums'
					};
				case 'albums':
					return {
						exampleInput: '4LH4d3cOWNNsVw41Gqt2kv',
						inputDescription: 'Spotify album ID',
						inputSchema: z.string(),
						inputsTableName: 'sp_api_albums'
					};
				case 'playlists':
					return {
						exampleInput: '37i9dQZF1DX5U26jySAO4K',
						inputDescription: 'Spotify playlist ID',
						inputSchema: z.string(),
						inputsTableName: 'sp_api_playlists'
					};
			}
	}
}
