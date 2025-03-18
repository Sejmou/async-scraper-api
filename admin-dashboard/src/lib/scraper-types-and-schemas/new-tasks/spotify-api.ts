import { z } from 'zod';
import type { ExpandRecursively } from '$lib/utils';

const regionSpecificParamsSchema = z.object({
	region: z.enum(['de', 'us'])
});

const spotifyIdsSchema = z.array(z.string().min(22).max(22));
const spotifyTaskInputsSchema = z.object({
	inputs: spotifyIdsSchema
});

const spotifyApiDataSourceSchema = z.object({
	dataSource: z.literal('spotify-api')
});

export const artistsPayloadSchema = spotifyTaskInputsSchema;
export type ArtistsPayload = ExpandRecursively<z.infer<typeof artistsPayloadSchema>>;
export const artistsTaskSchema = artistsPayloadSchema.and(spotifyApiDataSourceSchema).and(
	z.object({
		taskType: z.literal('artists')
	})
);
export type ArtistsTask = ExpandRecursively<z.infer<typeof artistsTaskSchema>>;

export const artistAlbumsParamsSchema = regionSpecificParamsSchema.extend({
	release_types: z.object({
		albums: z.boolean().default(false),
		singles: z.boolean().default(false),
		compilations: z.boolean().default(false),
		appears_on: z.boolean().default(false)
	})
});
export const artistAlbumsPayloadSchema = spotifyTaskInputsSchema.extend({
	params: artistAlbumsParamsSchema
});
export type ArtistAlbumsPayload = ExpandRecursively<z.infer<typeof artistAlbumsPayloadSchema>>;
export const artistAlbumsTaskSchema = artistAlbumsPayloadSchema.and(spotifyApiDataSourceSchema).and(
	z.object({
		taskType: z.literal('artist-albums')
	})
);
export type ArtistAlbumsTask = ExpandRecursively<z.infer<typeof artistAlbumsTaskSchema>>;

export const albumsParamsSchema = regionSpecificParamsSchema;
export const albumsPayloadSchema = spotifyTaskInputsSchema.extend({
	params: albumsParamsSchema
});
export type AlbumsPayload = ExpandRecursively<z.infer<typeof albumsPayloadSchema>>;
export const albumsTaskSchema = albumsPayloadSchema.and(spotifyApiDataSourceSchema).and(
	z.object({
		taskType: z.literal('albums')
	})
);
export type AlbumsTask = ExpandRecursively<z.infer<typeof albumsTaskSchema>>;

export const tracksParamsSchema = regionSpecificParamsSchema;
export type TracksParams = ExpandRecursively<z.infer<typeof tracksParamsSchema>>;
export const tracksPayloadSchema = spotifyTaskInputsSchema.extend({
	params: tracksParamsSchema
});
export type TracksPayload = ExpandRecursively<z.infer<typeof tracksPayloadSchema>>;
export const tracksTaskSchema = tracksPayloadSchema.and(spotifyApiDataSourceSchema).and(
	z.object({
		taskType: z.literal('tracks')
	})
);
export type TracksTask = ExpandRecursively<z.infer<typeof tracksTaskSchema>>;

export const playlistsPayloadSchema = spotifyTaskInputsSchema;
export type PlaylistsPayload = ExpandRecursively<z.infer<typeof playlistsPayloadSchema>>;
export const playlistsTaskSchema = playlistsPayloadSchema.and(spotifyApiDataSourceSchema).and(
	z.object({
		taskType: z.literal('playlists')
	})
);
export type PlaylistsTask = ExpandRecursively<z.infer<typeof playlistsTaskSchema>>;

export const spotifyApiTaskSchema = z.union([
	tracksTaskSchema,
	artistsTaskSchema,
	albumsTaskSchema,
	playlistsTaskSchema,
	artistAlbumsTaskSchema
]);
export type SpotifyAPITask = ExpandRecursively<z.infer<typeof spotifyApiTaskSchema>>;

export const spotifyApiTaskTypesSchema = z.union([
	z.literal('tracks'),
	z.literal('artists'),
	z.literal('albums'),
	z.literal('playlists'),
	z.literal('artist-albums')
]);
