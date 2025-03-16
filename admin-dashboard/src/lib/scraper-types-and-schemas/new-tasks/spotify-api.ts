import { z } from 'zod';

const regionSpecificParamsSchema = z.object({
	region: z.enum(['de', 'us'])
});

export const tracksParamsSchema = regionSpecificParamsSchema;
export type TracksParamsSchema = typeof tracksParamsSchema;
export const albumsParamsSchema = regionSpecificParamsSchema;
export type AlbumsParamsSchema = typeof albumsParamsSchema;
export const artistAlbumsParamsSchema = regionSpecificParamsSchema.extend({
	release_types: z.object({
		albums: z.boolean().default(false),
		singles: z.boolean().default(false),
		compilations: z.boolean().default(false),
		appears_on: z.boolean().default(false)
	})
});
export type ArtistAlbumsParamsSchema = typeof artistAlbumsParamsSchema;

export type SpotifyAPITask =
	| TracksTask
	| ArtistsTask
	| AlbumsTask
	| PlaylistsTask
	| ArtistAlbumsTask;

type SpotifyAPITaskBase = {
	dataSource: 'spotify-api';
};

type RegionSpecificParams = z.infer<typeof regionSpecificParamsSchema>;
type TracksTask = SpotifyAPITaskBase &
	RegionSpecificParams & {
		taskType: 'tracks';
		track_ids: string[];
	};

type ArtistsTask = SpotifyAPITaskBase & {
	taskType: 'artists';
	artist_ids: string[];
};

type AlbumsTask = SpotifyAPITaskBase &
	RegionSpecificParams & {
		taskType: 'albums';
		album_ids: string[];
	};

type PlaylistsTask = SpotifyAPITaskBase & {
	taskType: 'playlists';
	playlist_ids: string[];
};

type ArtistAlbumsParams = z.infer<typeof artistAlbumsParamsSchema>;
type ArtistAlbumsTask = SpotifyAPITaskBase &
	ArtistAlbumsParams & {
		taskType: 'artist-albums';
		artist_ids: string[];
	};
