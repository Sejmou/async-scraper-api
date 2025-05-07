import { z } from 'zod';

const jsonValueSchema: z.ZodType = z.lazy(() =>
	z.union([
		z.string(),
		z.number(),
		z.boolean(),
		z.null(),
		z.array(jsonValueSchema),
		z.record(jsonValueSchema)
	])
);

const dataFetchingTaskStatusSchema = z.union([
	z.literal('pending'),
	z.literal('running'),
	z.literal('done'),
	z.literal('error'),
	z.literal('pausing'),
	z.literal('paused')
]);
export type DataFetchingTaskStatus = z.infer<typeof dataFetchingTaskStatusSchema>;

export const dataSourceSchema = z.union([
	z.literal('spotify-api'),
	z.literal('spotify-internal'),
	z.literal('dummy-api')
]);
export type DataSource = z.infer<typeof dataSourceSchema>;

export const s3FileUploadSchema = z.object({
	id: z.number(),
	task_id: z.number(),
	s3_key: z.string(),
	s3_bucket: z.string(),
	s3_endpoint_url: z.string(),
	size_bytes: z.number(),
	uploaded_at: z.string().refine((val) => !isNaN(Date.parse(val)), {
		message: 'Invalid date format for uploaded_at'
	})
});

export const dataFetchingTaskSchema = z.object({
	id: z.number(),
	status: dataFetchingTaskStatusSchema,
	data_source: dataSourceSchema,
	task_type: z.string(),
	s3_prefix: z.string(),
	file_uploads: z.array(s3FileUploadSchema),
	params: z.record(jsonValueSchema).nullable(),
	created_at: z.string().refine((val) => !isNaN(Date.parse(val)), {
		message: 'Invalid date format for created_at'
	}),
	updated_at: z.string().refine((val) => !isNaN(Date.parse(val)), {
		message: 'Invalid date format for updated_at'
	}),
	batch_size: z.number()
});

export const tasksPageSchema = z.object({
	items: z.array(dataFetchingTaskSchema),
	page: z.number().int().positive(),
	size: z.number().int().positive(),
	total: z.number().int().nonnegative(),
	pages: z.number().int().positive()
});

export const taskProgressSchema = z.object({
	success_count: z.number(),
	failure_count: z.number(),
	inputs_without_output_count: z.number(),
	remaining_count: z.number()
});

export const deleteConfirmMessageSchema = z.object({
	message: z.string()
});

export type DataFetchingTask = z.infer<typeof dataFetchingTaskSchema>;
export type S3FileUpload = z.infer<typeof s3FileUploadSchema>;
export type TaskProgress = z.infer<typeof taskProgressSchema>;

const taskQueueItemSchema = z.object({
	id: z.number(),
	data: jsonValueSchema,
	added_at: z.string().refine((val) => !isNaN(Date.parse(val)), {
		message: 'Invalid date format for created_at'
	})
});
export const taskQueueItemsPageSchema = z.object({
	items: z.array(taskQueueItemSchema),
	next_cursor: z.number().int().positive().nullable(),
	total: z.number().int().nonnegative()
});

export const taskQueueTypeSchema = z.union([
	z.literal('remaining-inputs'),
	z.literal('successes'),
	z.literal('failures'),
	z.literal('inputs-without-output')
]);
export type TaskQueueType = z.infer<typeof taskQueueTypeSchema>;
