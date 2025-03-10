import { z } from 'zod';

const apiServerInfoSchema = z.object({
	version: z.string()
});

export type APIServerInfo = z.infer<typeof apiServerInfoSchema>;

export const getAPIServerInfo = async (url: string): Promise<APIServerInfo> => {
	const response = await fetch(`${url}/about`);
	const data = await response.json();
	return apiServerInfoSchema.parse(data);
};
