import { db } from '$lib/server/db';
import { server } from '$lib/server/db/schema';
import { asc } from 'drizzle-orm';
import { getAPIServerInfo } from '$lib/server/scraper-api/about';
import type { APIServerMeta } from './table-columns';

export async function load() {
	const serversInDb = await db.select().from(server).orderBy(asc(server.addedAt));
	type ServerMeta = (typeof serversInDb)[0];
	const getStatus = async (meta: ServerMeta) => {
		try {
			const { version } = await getAPIServerInfo(meta);
			return { version, online: true };
		} catch {
			return { version: null, online: false };
		}
	};

	const serverMeta: APIServerMeta[] = await Promise.all(
		serversInDb.map(async (server) => {
			const { version, online } = await getStatus(server);
			return {
				ip_and_port: `${server.host}:${server.port}`,
				version,
				online
			};
		})
	);
	return {
		servers: serverMeta
	};
}
