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
	z.literal('paused')
]);

const dataSourceSchema = z.literal('spotify-api');

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

export type DataFetchingTask = z.infer<typeof dataFetchingTaskSchema>;
export type S3FileUpload = z.infer<typeof s3FileUploadSchema>;
