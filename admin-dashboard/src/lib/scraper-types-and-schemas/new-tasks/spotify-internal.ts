import { z } from 'zod';
import type { ExpandRecursively } from '$lib/utils';
import type { ParamsUnion, SupportedTaskCandidate, TaskInputMeta } from '.';

const spotifyIdsSchema = z.array(z.string().min(22).max(22));
const spotifyTaskInputsSchema = z.object({
	inputs: spotifyIdsSchema
});

const spotifyInternalApiDataSourceSchema = z.object({
	dataSource: z.literal('spotify-internal')
});

export const relatedArtistsPayloadSchema = spotifyTaskInputsSchema;
export type RelatedArtistsPayload = ExpandRecursively<z.infer<typeof relatedArtistsPayloadSchema>>;
export const relatedArtistsTaskSchema = relatedArtistsPayloadSchema
	.and(spotifyInternalApiDataSourceSchema)
	.and(
		z.object({
			taskType: z.literal('related-artists')
		})
	);
export type RelatedArtistsTask = ExpandRecursively<z.infer<typeof relatedArtistsTaskSchema>>;
const initialRelatedArtistsTask: RelatedArtistsTask = {
	dataSource: 'spotify-internal',
	taskType: 'related-artists',
	inputs: []
};

export const spotifyInternalApiTaskSchema = relatedArtistsTaskSchema;
// = z.union([
// 	relatedArtistsTaskSchema,
//  TODO: add more
// ]);
export type SpotifyInternalAPITask = ExpandRecursively<
	z.infer<typeof spotifyInternalApiTaskSchema>
>;

export const spotifyInternalApiTaskTypesSchema = z.literal('related-artists');
//  = z.union([
// 	z.literal('related-artists'),
//  TODO: add more
// ]);

export type SupportedSpotifyInternalAPITaskCandidate = Extract<
	SupportedTaskCandidate,
	{ dataSource: 'spotify-internal' }
>;

export const parseSpotifyInternalTask = (candidate: SupportedSpotifyInternalAPITaskCandidate) => {
	switch (candidate.taskType) {
		case 'related-artists':
			return relatedArtistsTaskSchema.parse(candidate);
	}
};

export const getInitialSpotifyInternalTask = (
	taskType: SpotifyInternalAPITask['taskType']
): SpotifyInternalAPITask => {
	switch (taskType) {
		case 'related-artists':
			return initialRelatedArtistsTask;
	}
};

export type SpotifyInternalAPITaskType = SpotifyInternalAPITask['taskType'];
export type SpotifyInternalAPITaskInput = SpotifyInternalAPITask['inputs'][0];

export const getSpotifyInternalTaskInputMeta = (
	taskType: SpotifyInternalAPITaskType
): TaskInputMeta<SpotifyInternalAPITaskInput> => {
	switch (taskType) {
		case 'related-artists':
			return {
				exampleInput: '4PTG3Z6ehGkBFwjybzWkR8',
				inputsDescription: 'Spotify artist IDs',
				inputSchema: z.string(),
				inputsTableName: 'sp_api_artist_albums'
			};
	}
};

export const getSpotifyInternalTaskParamsSchema = (
	task: Pick<SupportedSpotifyInternalAPITaskCandidate, 'dataSource' | 'taskType'>
): z.ZodSchema<ParamsUnion<SpotifyInternalAPITask>> | null => {
	switch (task.taskType) {
		case 'related-artists':
			return null;
	}
};
