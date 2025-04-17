import { createTransaction, db } from '$lib/server/db';
import { scraperServerTbl, type ScraperInsert } from '$lib/server/db/schema';
import { asc, eq } from 'drizzle-orm';
import { getScraperServerMetadata } from '$lib/server/scraper-api/get-server-metadata';
import type { ScraperMetadata } from './table-columns';
import { superValidate, message } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import { formSchemaBatchImport, formSchemaSingleInsert, baseUrlSchema } from './form-schema';
import { fail } from '@sveltejs/kit';

export async function load() {
	const scrapers = await db.select().from(scraperServerTbl).orderBy(asc(scraperServerTbl.addedAt));

	const scraperMeta: ScraperMetadata[] = await Promise.all(
		scrapers.map(async (scraper) => {
			const infoRes = await getScraperServerMetadata(scraper);
			const version = infoRes.status === 'error' ? null : infoRes.data.version;
			const online = infoRes.status === 'error' ? false : true;
			return {
				id: scraper.id,
				host: `${scraper.protocol}://${scraper.host}:${scraper.port}`,
				version,
				online
			};
		})
	);

	return {
		servers: scraperMeta,
		singleInsertForm: await superValidate(zod(formSchemaSingleInsert)),
		batchInsertForm: await superValidate(zod(formSchemaBatchImport))
	};
}

type ServerInsertMeta = ScraperInsert & {
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
			await db.insert(scraperServerTbl).values(insert);
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

		try {
			const databaseTransaction = createTransaction(db);
			await databaseTransaction.transaction(async ({ db, rollback }) => {
				for (const value of valuesToInsert) {
					try {
						await db.insert(scraperServerTbl).values(value);
					} catch (e) {
						console.error('Error inserting server', value, e);
						rollback();
					}
				}
			});
		} catch {
			return message(
				form,
				{
					type: 'error',
					text: `Error while inserting into DB. Make sure that no server with the same host and port exists in the DB and the URLs you provided.`
				},
				{ status: 400 }
			);
		}

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
		await db.delete(scraperServerTbl).where(eq(scraperServerTbl.id, +id));
		return { success: true };
	}
};
