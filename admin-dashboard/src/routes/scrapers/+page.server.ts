import { db } from '$lib/server/db';
import { server, type ServerInsert } from '$lib/server/db/schema';
import { asc, eq } from 'drizzle-orm';
import { getAPIServerInfo } from '$lib/server/scraper-api/about';
import type { APIServerMeta } from './table-columns';
import { superValidate, message } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import { formSchemaBatchImport, formSchemaSingleInsert, baseUrlSchema } from './form-schema';
import { fail } from '@sveltejs/kit';

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
				id: server.id,
				host: `${server.protocol}://${server.host}:${server.port}`,
				version,
				online
			};
		})
	);

	return {
		servers: serverMeta,
		singleInsertForm: await superValidate(zod(formSchemaSingleInsert)),
		batchInsertForm: await superValidate(zod(formSchemaBatchImport))
	};
}

type ServerInsertMeta = ServerInsert & {
	originalInput: string;
};

const validServerUrlStringToInsertMeta: (urlStr: string) => ServerInsertMeta = (urlStr) => {
	const urlObj = new URL(urlStr);
	// port property of URL object is empty string if port is equal to default port of protocol (80 for http, 443 for https)
	const port = urlObj.port ? +urlObj.port : urlObj.protocol === 'https:' ? 443 : 80;
	return {
		host: urlObj.hostname,
		port,
		protocol: urlObj.protocol.replace(':', ''),
		originalInput: urlStr
	};
};

export const actions = {
	'add-one': async (event) => {
		const form = await superValidate(event, zod(formSchemaSingleInsert));
		if (!form.valid) {
			return message(form, {
				type: 'error',
				text: 'The data you provided is invalid'
			});
		}

		const insert = validServerUrlStringToInsertMeta(form.data.baseUrl);
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
		const form = await superValidate(request, zod(formSchemaBatchImport));
		if (!form.valid) {
			return message(form, {
				type: 'error',
				text: 'The data you provided is invalid. Please provide a list of valid URLs, separated by newlines.'
			});
		}

		const urlStrings = form.data.baseUrls
			.split('\n')
			.map((str) => str.trim())
			.filter((str) => str !== '');

		const valuesToInsert: ServerInsertMeta[] = [];
		const invalidInputs: string[] = [];
		for (const urlStr of urlStrings) {
			const zodParseRes = baseUrlSchema.safeParse(urlStr);
			if (!zodParseRes.success) {
				invalidInputs.push(urlStr);
				continue;
			}
			valuesToInsert.push(validServerUrlStringToInsertMeta(urlStr));
		}
		if (invalidInputs.length > 0) {
			return message(form, {
				type: 'error',
				text: `The following inputs could not be processed:\n${invalidInputs.join(', ')}`
			});
		}

		await db.transaction(async (trx) => {
			for (const value of valuesToInsert) {
				try {
					await trx.insert(server).values(value);
				} catch (e) {
					console.error('Error inserting server', value, e);
					trx.rollback();
					return message(
						form,
						{
							type: 'error',
							text: `Error while inserting '${value.originalInput}' into DB. Make sure that no server with the same host and port exists in the DB and the URLs you provided.`
						},
						{ status: 400 }
					);
				}
			}
		});

		return message(form, {
			type: 'success',
			text: `Successfully inserted ${valuesToInsert.length} servers into the DB`
		});
	},
	delete: async ({ request }) => {
		const data = await request.formData();
		const id = data.get('id');
		if (!id) {
			return fail(400);
		}
		await db.delete(server).where(eq(server.id, +id));
	}
};
