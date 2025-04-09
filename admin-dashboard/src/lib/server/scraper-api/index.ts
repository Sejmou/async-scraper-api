import { type Scraper as Scraper } from '$lib/server/db/schema';
import { z, type ZodTypeAny } from 'zod';

type ScraperRequestDataBase<S extends ZodTypeAny> = {
	scraper: Scraper;
	path: string;
	params?: Record<string, string | number | boolean>;
	responseSchema: S;
};

type ScraperGetRequestData<S extends ZodTypeAny> = ScraperRequestDataBase<S> & {
	method: 'GET';
};

type ScraperPostRequestData<S extends ZodTypeAny> = ScraperRequestDataBase<S> & {
	method: 'POST';
	body?: Record<string, unknown>;
};

type ScraperRequestData<S extends ZodTypeAny> =
	| ScraperGetRequestData<S>
	| ScraperPostRequestData<S>;

export const makeRequestToScraper = async <S extends ZodTypeAny>(
	reqData: ScraperRequestData<S>
): Promise<
	| {
			status: 'success';
			data: z.infer<S>;
	  }
	| {
			status: 'error';
			error: Record<string, unknown>;
	  }
> => {
	const { scraper, path, params, method, responseSchema } = reqData;
	const queryString = params
		? '?' +
			Object.entries(params)
				.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
				.join('&')
		: '';
	const pathWithParams = path + queryString;
	const url = `${scraper.protocol}://${scraper.host}:${scraper.port}/${pathWithParams}`;

	try {
		const res = await fetch(url, {
			method,
			headers: {
				'Content-Type': 'application/json'
			},
			body: reqData.method === 'POST' && reqData.body ? JSON.stringify(reqData.body) : undefined
		});
		const data = await res.json();
		if (!res.ok) {
			console.error(`Request to scraper API endpoint failed`, reqData);
			return {
				status: 'error',
				error: data
			};
		}
		const schemaParseRes = responseSchema.safeParse(data);
		if (!schemaParseRes.success) {
			console.error(`Response from scraper API endpoint did not match expected schema`, {
				data,
				validationError: schemaParseRes.error
			});
			return {
				status: 'error',
				error: {
					message: 'Response from scraper API endpoint did not match expected schema'
				}
			};
		}
		return {
			status: 'success',
			data: schemaParseRes.data
		};
	} catch (e) {
		console.error(`Error sending request to scraper API endpoint`, {
			scraper,
			reqData,
			error: e
		});
		return {
			status: 'error',
			error: {
				message: 'Error sending request to scraper API endpoint'
			}
		};
	}
};
