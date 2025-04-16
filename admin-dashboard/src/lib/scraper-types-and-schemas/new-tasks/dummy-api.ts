import { z } from 'zod';
import type { ExpandRecursively } from '$lib/utils';
import type { ParamsUnion, SupportedTaskCandidate, TaskInputMeta } from '.';

const dummyApiIdsSchema = z.array(z.number().int().positive());
const dummyApiTaskInputsSchema = z.object({
	inputs: dummyApiIdsSchema
});

const dummyApiDataSourceSchema = z.object({
	dataSource: z.literal('dummy-api')
});

export const flakyTaskParamsSchema = z.object({
	flakiness: z.number().min(0).max(1)
});
export type FlakyTaskParams = ExpandRecursively<z.infer<typeof flakyTaskParamsSchema>>;
export const flakyTaskPayloadSchema = dummyApiTaskInputsSchema.extend({
	params: flakyTaskParamsSchema
});
export type FlakyTaskPayload = ExpandRecursively<z.infer<typeof flakyTaskPayloadSchema>>;
export const flakyTaskSchema = flakyTaskPayloadSchema.and(dummyApiDataSourceSchema).and(
	z.object({
		taskType: z.literal('flaky')
	})
);
export type FlakyTask = ExpandRecursively<z.infer<typeof flakyTaskSchema>>;
export const initialFlakyTask: FlakyTask = {
	dataSource: 'dummy-api',
	taskType: 'flaky',
	inputs: [],
	params: {
		flakiness: 0.1
	}
};

export const throwAboveThresholdTaskParamsSchema = z.object({
	threshold: z.number().int().positive()
});
export type ThrowAboveThresholdTaskParams = ExpandRecursively<
	z.infer<typeof throwAboveThresholdTaskParamsSchema>
>;
export const throwAboveThresholdTaskPayloadSchema = dummyApiTaskInputsSchema.extend({
	params: throwAboveThresholdTaskParamsSchema
});
export type ThrowAboveThresholdTaskPayload = ExpandRecursively<
	z.infer<typeof throwAboveThresholdTaskPayloadSchema>
>;
export const throwAboveThresholdTaskSchema = throwAboveThresholdTaskPayloadSchema
	.and(dummyApiDataSourceSchema)
	.and(
		z.object({
			taskType: z.literal('throw-above-threshold')
		})
	);
export type ThrowAboveThresholdTask = ExpandRecursively<
	z.infer<typeof throwAboveThresholdTaskSchema>
>;
export const initialThrowAboveThresholdTask: ThrowAboveThresholdTask = {
	dataSource: 'dummy-api',
	taskType: 'throw-above-threshold',
	inputs: [],
	params: {
		threshold: 10
	}
};

export const dummyApiTaskSchema = z.union([flakyTaskSchema, throwAboveThresholdTaskSchema]);
export type DummyAPITask = ExpandRecursively<z.infer<typeof dummyApiTaskSchema>>;

export const dummyApiTaskTypesSchema = z.union([
	z.literal('flaky'),
	z.literal('throw-above-threshold')
]);

export type SupportedDummyAPITaskCandidate = Extract<
	SupportedTaskCandidate,
	{ dataSource: 'dummy-api' }
>;

export const parseDummyTask = (candidate: SupportedDummyAPITaskCandidate) => {
	switch (candidate.taskType) {
		case 'flaky':
			return flakyTaskSchema.parse(candidate);
		case 'throw-above-threshold':
			return throwAboveThresholdTaskSchema.parse(candidate);
	}
};

export const getInitialDummyTask = (taskType: DummyAPITask['taskType']): DummyAPITask => {
	switch (taskType) {
		case 'flaky':
			return initialFlakyTask;
		case 'throw-above-threshold':
			return initialThrowAboveThresholdTask;
	}
};

export type DummyAPITaskType = DummyAPITask['taskType'];
export type DummyAPITaskInput = DummyAPITask['inputs'][0];

export const getDummyTaskInputMeta = (
	taskType: DummyAPITaskType
): TaskInputMeta<DummyAPITaskInput> => {
	switch (taskType) {
		case 'flaky':
			return {
				exampleInput: 69,
				inputsDescription: 'dummy IDs aka positive integers',
				inputSchema: z.number().int().positive(),
				inputsTableName: 'dummy_api_flaky'
			};
		case 'throw-above-threshold':
			return {
				exampleInput: 42,
				inputsDescription: 'dummy IDs aka positive integers',
				inputSchema: z.number().int().positive(),
				inputsTableName: 'dummy_api_throw_above_threshold'
			};
	}
};

export const getDummyTaskParamsSchema = (
	task: Pick<SupportedDummyAPITaskCandidate, 'dataSource' | 'taskType'>
): z.ZodSchema<ParamsUnion<DummyAPITask>> | null => {
	switch (task.taskType) {
		case 'flaky':
			return flakyTaskParamsSchema;
		case 'throw-above-threshold':
			return throwAboveThresholdTaskParamsSchema;
	}
};
