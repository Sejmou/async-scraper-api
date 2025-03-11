import { z } from 'zod';

const baseUrlSchema = z.string().refine(
	(val) => {
		try {
			const parsed = new URL(val);
			// Check that the protocol is http or https,
			// and that a port is specified (non-empty string)
			return (
				(parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
				!!parsed.hostname &&
				parsed.port !== '' &&
				parsed.pathname == '/'
			);
		} catch {
			return false;
		}
	},
	{
		message: 'Invalid base URL: must be http/https, include a hostname (or IP), port, and no path'
	}
);

export const formSchema = z.object({
	baseUrl: baseUrlSchema
});

export type FormSchema = typeof formSchema;

export const formSchemaBatchInsert = z.array(baseUrlSchema);
