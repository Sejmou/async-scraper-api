import { db } from '$lib/server/db';
import { server, type ServerInsert } from '$lib/server/db/schema';
import { asc } from 'drizzle-orm';
import { getAPIServerInfo } from '$lib/server/scraper-api/about';
import type { APIServerMeta } from './table-columns';
import { superValidate, message } from 'sveltekit-superforms';
import { fail } from '@sveltejs/kit';
import { zod } from 'sveltekit-superforms/adapters';
import { formSchema, formSchemaBatchInsert } from './form-schema';

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
				host: `${server.protocol}://${server.host}:${server.port}`,
				version,
				online
			};
		})
	);
	return {
		servers: serverMeta,
		form: await superValidate(zod(formSchema))
	};
}

const parseServerUrlString: (urlStr: string) => ServerInsert & {
	originalInput: string;
} = (urlStr) => {
	const urlObj = new URL(urlStr);
	return {
		host: urlObj.hostname,
		port: +urlObj.port,
		protocol: urlObj.protocol.replace(':', ''),
		originalInput: urlStr
	};
};

export const actions = {
	'add-one': async (event) => {
		const form = await superValidate(event, zod(formSchema));
		if (!form.valid) {
			return message(form, {
				type: 'error',
				text: 'The data you provided is invalid'
			});
		}

		const insert = parseServerUrlString(form.data.baseUrl);
		try {
			await db.insert(server).values(insert);
		} catch (e) {
			if (e && typeof e === 'object' && 'code' in e && e.code === 'SQLITE_CONSTRAINT_UNIQUE') {
				return message(
					form,
					{
						type: 'error',
						text: `Server with host '${insert.host}' and port ${insert.port} already exists in the DB`
					},
					{
						status: 400
					}
				);
			} else {
				return message(
					form,
					{ type: 'error', text: 'An unexpected error occured while inserting server into DB' },
					{
						status: 500
					}
				);
			}
		}

		return { form };
	},
	'batch-import': async ({ request }) => {
		const data = await request.formData();
		const scraperUrlsRaw = data.get('scraper-urls')?.toString().split('\n');
		if (!scraperUrlsRaw) {
			return fail(400, { message: 'No URLs provided' });
		}
		const result = formSchemaBatchInsert.safeParse(scraperUrlsRaw);

		if (!result.success) {
			// result.error.issues is an array of error objects
			const errors = result.error.issues;
			const errorMessages = errors.map((issue) => {
				// The path should indicate the index in the array where the error occurred.
				const index = issue.path[0];
				const lineNumber = typeof index === 'number' ? index + 1 : 'unknown';
				return `Line ${lineNumber}: ${issue.message}`;
			});
			const invalidCount = errors.length;
			return fail(400, {
				message: `${invalidCount} URL${invalidCount === 1 ? '' : 's'} ${invalidCount === 1 ? 'is' : 'are'} invalid:\n${errorMessages.join('\n')}`
			});
		}
		const urls = result.data;
		const insertValues = urls.map(parseServerUrlString);

		await db.transaction(async (trx) => {
			for (const insert of insertValues) {
				try {
					await trx.insert(server).values(insert);
				} catch (e) {
					console.error('Error inserting server', insert, e);
					trx.rollback();
					return fail(400, {
						message: `Error while inserting '${insert.originalInput}' into DB. Make sure that no server with the same host and port exists in the DB and the URLs you provided.`
					});
				}
			}
		});

		return { message: 'Success' };
	}
};
