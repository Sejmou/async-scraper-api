import { z } from 'zod';

// --- Input Items Schemas ---

export const tracksInputItemsSchema = z.object({
	track_ids: z.array(z.string())
});

export const artistsInputItemsSchema = z.object({
	artist_ids: z.array(z.string())
});

export const albumsInputItemsSchema = z.object({
	album_ids: z.array(z.string())
});

export const playlistsInputItemsSchema = z.object({
	playlist_ids: z.array(z.string())
});

export const isrcsInputItemsSchema = z.object({
	isrcs: z.array(z.string())
});

// --- Shared Region Specific Params Schema ---

const regionSpecificParamsSchema = z.object({
	region: z.enum(['de', 'us']).nullable().optional()
});

// --- Specific Params Schemas ---

export const tracksParamsSchema = regionSpecificParamsSchema; // no extra fields
export const albumsParamsSchema = regionSpecificParamsSchema; // no extra fields
export const isrcTrackSearchParamsSchema = regionSpecificParamsSchema; // no extra fields

export const artistAlbumsParamsSchema = regionSpecificParamsSchema.extend({
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
export const artistsPayloadSchema = artistsInputItemsSchema;
export const albumsPayloadSchema = albumsInputItemsSchema.merge(albumsParamsSchema);
export const artistAlbumsPayloadSchema = artistsInputItemsSchema.merge(artistAlbumsParamsSchema);
export const playlistsPayloadSchema = playlistsInputItemsSchema;
export const isrcTrackSearchPayloadSchema = isrcsInputItemsSchema.merge(
	isrcTrackSearchParamsSchema
);
