import { type ExpandRecursively } from '$lib/utils';
import { z } from 'zod';
import {
	albumsTaskSchema,
	artistAlbumsTaskSchema,
	artistsTaskSchema,
	playlistsTaskSchema,
	tracksTaskSchema,
	spotifyApiTaskTypesSchema
} from './spotify-api';

export const scraperSchema = z.object({
	host: z.string(),
	port: z.number(),
	protocol: z.string()
});
export type Scraper = z.infer<typeof scraperSchema>;

export const taskSchema = z.discriminatedUnion('dataSource', [
	z.object({
		dataSource: z.literal('spotify-api'),
		taskType: spotifyApiTaskTypesSchema,
		inputs: z.array(z.unknown()),
		params: z.record(z.unknown()).optional()
	})
]);

export const parseToTaskOrThrowError = (input: unknown) => {
	const result = taskSchema.parse(input);
	switch (result.dataSource) {
		case 'spotify-api':
			switch (result.taskType) {
				case 'tracks':
					return tracksTaskSchema.parse(result);
				case 'artists':
					return artistsTaskSchema.parse(result);
				case 'albums':
					return albumsTaskSchema.parse(result);
				case 'artist-albums':
					return artistAlbumsTaskSchema.parse(result);
				case 'playlists':
					return playlistsTaskSchema.parse(result);
			}
	}
};

export type SupportedTask = ExpandRecursively<ReturnType<typeof parseToTaskOrThrowError>>;
