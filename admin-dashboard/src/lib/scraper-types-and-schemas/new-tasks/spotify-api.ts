import { z } from 'zod';
import type { ExpandRecursively } from '$lib/utils';
import type { ParamsUnion, SupportedTaskCandidate, TaskInputMeta } from '.';

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
const initialArtistsTask: ArtistsTask = {
	dataSource: 'spotify-api',
	taskType: 'artists',
	inputs: []
};

export const artistAlbumsParamsSchema = regionSpecificParamsSchema.extend({
	release_types: z.object({
		albums: z.boolean().default(false),
		singles: z.boolean().default(false),
		compilations: z.boolean().default(false),
		appears_on: z.boolean().default(false)
	})
});
export type ArtistAlbumsParams = ExpandRecursively<z.infer<typeof artistAlbumsParamsSchema>>;
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
const initialArtistAlbumsTask: ArtistAlbumsTask = {
	dataSource: 'spotify-api',
	taskType: 'artist-albums',
	inputs: [],
	params: {
		region: 'de',
		release_types: {
			albums: true,
			singles: false,
			compilations: false,
			appears_on: false
		}
	}
};

export const albumsParamsSchema = regionSpecificParamsSchema;
export type AlbumsParams = ExpandRecursively<z.infer<typeof albumsParamsSchema>>;
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
const initialAlbumsTask: AlbumsTask = {
	dataSource: 'spotify-api',
	taskType: 'albums',
	inputs: [],
	params: {
		region: 'de'
	}
};

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
const initialTracksTask: TracksTask = {
	dataSource: 'spotify-api',
	taskType: 'tracks',
	inputs: [],
	params: {
		region: 'de'
	}
};

export const playlistsPayloadSchema = spotifyTaskInputsSchema;
export type PlaylistsPayload = ExpandRecursively<z.infer<typeof playlistsPayloadSchema>>;
export const playlistsTaskSchema = playlistsPayloadSchema.and(spotifyApiDataSourceSchema).and(
	z.object({
		taskType: z.literal('playlists')
	})
);
export type PlaylistsTask = ExpandRecursively<z.infer<typeof playlistsTaskSchema>>;
const initialPlaylistsTask: PlaylistsTask = {
	dataSource: 'spotify-api',
	taskType: 'playlists',
	inputs: []
};

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

type SupportedSpotifyTaskCandidate = Extract<SupportedTaskCandidate, { dataSource: 'spotify-api' }>;

export const parseSpotifyTask = (candidate: SupportedSpotifyTaskCandidate) => {
	switch (candidate.taskType) {
		case 'tracks':
			return tracksTaskSchema.parse(candidate);
		case 'artists':
			return artistsTaskSchema.parse(candidate);
		case 'albums':
			return albumsTaskSchema.parse(candidate);
		case 'artist-albums':
			return artistAlbumsTaskSchema.parse(candidate);
		case 'playlists':
			return playlistsTaskSchema.parse(candidate);
	}
};

export const getInitialSpotifyTask = (taskType: SpotifyAPITask['taskType']): SpotifyAPITask => {
	switch (taskType) {
		case 'tracks':
			return initialTracksTask;
		case 'artists':
			return initialArtistsTask;
		case 'albums':
			return initialAlbumsTask;
		case 'playlists':
			return initialPlaylistsTask;
		case 'artist-albums':
			return initialArtistAlbumsTask;
	}
};

export type SpotifyAPITaskType = SpotifyAPITask['taskType'];
export type SpotifyAPITaskInput = SpotifyAPITask['inputs'][0];

export const getSpotifyTaskInputMeta = (
	taskType: SpotifyAPITaskType
): TaskInputMeta<SpotifyAPITaskInput> => {
	switch (taskType) {
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
};

export const getSpotifyTaskParamsSchema = (
	task: Pick<SupportedSpotifyTaskCandidate, 'dataSource' | 'taskType'>
): z.ZodSchema<ParamsUnion<SpotifyAPITask>> | null => {
	switch (task.taskType) {
		case 'artists':
			return null;
		case 'tracks':
			return tracksParamsSchema;
		case 'artist-albums':
			return artistAlbumsParamsSchema;
		case 'albums':
			return albumsParamsSchema;
		case 'playlists':
			return null;
	}
};
