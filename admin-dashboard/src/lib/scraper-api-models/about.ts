import { z } from 'zod';

export const aboutSchema = z.object({
	version: z.string()
});
