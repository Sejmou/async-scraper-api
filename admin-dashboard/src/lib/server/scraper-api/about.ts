import { z } from 'zod';

const apiServerInfoSchema = z.object({
	version: z.string()
});

export type APIServerInfo = z.infer<typeof apiServerInfoSchema>;

export const getAPIServerInfo = async (meta: {
	host: string;
	port: number;
	protocol: string;
}): Promise<APIServerInfo> => {
	const { host, port, protocol } = meta;
	const url = `${protocol}://${host}:${port}/about`;
	const response = await fetch(url);
	const data = await response.json();
	return apiServerInfoSchema.parse(data);
};
