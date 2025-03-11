import { z } from 'zod';

export const baseUrlSchema = z.string().refine(
	(val) => {
		try {
			const parsed = new URL(val);
			// Check that the protocol is http or https,
			// and that a port is specified (non-empty string)
			return (
				(parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
				!!parsed.hostname &&
				// if port equals default port for protocol (i.e. 80 for http, 443 for https), it will be omitted, hence checking makes no sense
				// parsed.port !== '' &&
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

export const formSchemaSingleInsert = z.object({
	baseUrl: baseUrlSchema
});

export const formSchemaBatchImport = z.object({
	// should be a string containing valid base URLS, separated by '\n'; not sure if zod makes it possible to validate this
	baseUrls: z.string()
});

export type FormSchemaSingleInsert = typeof formSchemaSingleInsert;
export type FormSchemaBatchImport = typeof formSchemaBatchImport;
