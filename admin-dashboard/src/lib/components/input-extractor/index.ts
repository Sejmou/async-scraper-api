import Root from './root.svelte';
import { z } from 'zod';

export type FileColumnPreviewColumns = { name: string; type: string };

export const extractedColumnsSchema = z.array(
	z.object({
		column_name: z.string(),
		column_type: z.string()
	})
);

export { Root, Root as InputExtractor };
