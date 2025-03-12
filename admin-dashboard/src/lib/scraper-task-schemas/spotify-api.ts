import { z } from 'zod';

// --- Input Items Schemas ---

const tracksInputItemsSchema = z.object({
	track_ids: z.array(z.string())
});

const artistsInputItemsSchema = z.object({
	artist_ids: z.array(z.string())
});

const albumsInputItemsSchema = z.object({
	album_ids: z.array(z.string())
});

const playlistsInputItemsSchema = z.object({
	playlist_ids: z.array(z.string())
});

const isrcsInputItemsSchema = z.object({
	isrcs: z.array(z.string())
});

// --- Shared Region Specific Params Schema ---

const regionSpecificParamsSchema = z.object({
	region: z.enum(['de', 'us']).nullable().optional()
});

// --- Specific Params Schemas ---

const tracksParamsSchema = regionSpecificParamsSchema; // no extra fields
const albumsParamsSchema = regionSpecificParamsSchema; // no extra fields
const isrcTrackSearchParamsSchema = regionSpecificParamsSchema; // no extra fields

const artistAlbumsParamsSchema = regionSpecificParamsSchema.extend({
	release_types: z.object({
		albums: z.boolean().default(false),
		singles: z.boolean().default(false),
		compilations: z.boolean().default(false),
		appears_on: z.boolean().default(false)
	})
});

// --- Payload Schemas ---

// Payloads combine input items and optional params via merging.
export const tracksPayloadSchema = tracksInputItemsSchema.merge(tracksParamsSchema);
export type TracksPayloadSchema = typeof tracksPayloadSchema;
export const artistsPayloadSchema = artistsInputItemsSchema;
export type ArtistsPayloadSchema = typeof artistsPayloadSchema;
export const albumsPayloadSchema = albumsInputItemsSchema.merge(albumsParamsSchema);
export const artistAlbumsPayloadSchema = artistsInputItemsSchema.merge(artistAlbumsParamsSchema);
export const playlistsPayloadSchema = playlistsInputItemsSchema;
export const isrcTrackSearchPayloadSchema = isrcsInputItemsSchema.merge(
	isrcTrackSearchParamsSchema
);
