import { z } from 'zod';

const regionSpecificParamsSchema = z.object({
	region: z.enum(['de', 'us'])
});

export const tracksParamsSchema = regionSpecificParamsSchema;
export type TracksParamsSchema = typeof tracksParamsSchema;
export const tracksPayloadSchema = tracksParamsSchema.extend({
	track_ids: z.array(z.string())
});
export type TracksPayload = z.infer<typeof tracksPayloadSchema>;

export const albumsParamsSchema = regionSpecificParamsSchema;
export type AlbumsParamsSchema = typeof albumsParamsSchema;
export const albumsPayloadSchema = albumsParamsSchema.extend({
	album_ids: z.array(z.string())
});
export type AlbumsPayload = z.infer<typeof albumsPayloadSchema>;

export const artistAlbumsParamsSchema = regionSpecificParamsSchema.extend({
	release_types: z.object({
		albums: z.boolean().default(false),
		singles: z.boolean().default(false),
		compilations: z.boolean().default(false),
		appears_on: z.boolean().default(false)
	})
});
export type ArtistAlbumsParamsSchema = typeof artistAlbumsParamsSchema;
export const artistAlbumsPayloadSchema = artistAlbumsParamsSchema.extend({
	artist_ids: z.array(z.string())
});
export type ArtistAlbumsPayload = z.infer<typeof artistAlbumsPayloadSchema>;

export const artistsPayloadSchema = z.object({
	artist_ids: z.array(z.string())
});
export type ArtistsPayload = z.infer<typeof artistsPayloadSchema>;

export const playlistsPayloadSchema = z.object({
	playlist_ids: z.array(z.string())
});
export type PlaylistsPayload = z.infer<typeof playlistsPayloadSchema>;

export type SpotifyAPITask =
	| TracksTask
	| ArtistsTask
	| AlbumsTask
	| PlaylistsTask
	| ArtistAlbumsTask;

const spotifyTaskBaseSchema = z.object({
	dataSource: z.literal('spotify-api')
});

export const tracksTaskSchema = spotifyTaskBaseSchema.extend({
	taskType: z.literal('tracks'),
	payload: tracksPayloadSchema
});
export type TracksTask = z.infer<typeof tracksTaskSchema>;

export const artistsTaskSchema = spotifyTaskBaseSchema.extend({
	taskType: z.literal('artists'),
	payload: artistsPayloadSchema
});
export type ArtistsTask = typeof artistsTaskSchema;

export const albumsTaskSchema = spotifyTaskBaseSchema.extend({
	taskType: z.literal('albums'),
	payload: albumsPayloadSchema
});
export type AlbumsTask = z.infer<typeof albumsTaskSchema>;

export const playlistsTaskSchema = spotifyTaskBaseSchema.extend({
	taskType: z.literal('playlists'),
	payload: playlistsPayloadSchema
});
export type PlaylistsTask = z.infer<typeof playlistsTaskSchema>;

export const artistAlbumsTaskSchema = spotifyTaskBaseSchema.extend({
	taskType: z.literal('artist-albums'),
	payload: artistAlbumsPayloadSchema
});
export type ArtistAlbumsTask = z.infer<typeof artistAlbumsTaskSchema>;
