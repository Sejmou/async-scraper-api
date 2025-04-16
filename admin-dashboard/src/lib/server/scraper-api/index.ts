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

export const constructScraperRequestUrl = (
	scraper: Scraper,
	path: string,
	params?: Record<string, string | number | boolean>
): string => {
	const queryString = params
		? '?' +
			Object.entries(params)
				.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
				.join('&')
		: '';
	const pathWithParams = path + queryString;
	return `${scraper.protocol}://${scraper.host}:${scraper.port}/${pathWithParams}`;
};

export const makeRequestToScraper = async <S extends ZodTypeAny>(
	requestData: ScraperRequestData<S>
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
	const { scraper, path, params, method, responseSchema } = requestData;
	const url = constructScraperRequestUrl(scraper, path, params);

	try {
		const res = await fetch(url, {
			method,
			headers: {
				'Content-Type': 'application/json'
			},
			body:
				requestData.method === 'POST' && requestData.body
					? JSON.stringify(requestData.body)
					: undefined
		});
		const data = await res.json();
		if (!res.ok) {
			console.error(`Request to scraper API endpoint failed`, requestData);
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
		// remove responseSchema as it isn't relevant for handling errors (they cannot be related to schema validation!)
		// eslint-disable-next-line @typescript-eslint/no-unused-vars
		const { responseSchema, ...data } = requestData;
		if (e instanceof TypeError) {
			if (
				e.cause &&
				typeof e.cause === 'object' &&
				'code' in e.cause &&
				e.cause.code === 'ECONNREFUSED'
			) {
				console.warn(`Request to ${url} failed (scraper is probably offline)`, {
					scraper,
					requestData: {
						data
					}
				});
			} else {
				console.error(`Network error sending request to scraper API endpoint`, {
					scraper,
					requestData: data,
					error: e
				});
			}
		} else {
			console.error(`Unknown error sending request to scraper API endpoint`, {
				scraper,
				requestData: data,
				error: e
			});
		}
		return {
			status: 'error',
			error: {
				message: 'Error sending request to scraper API endpoint'
			}
		};
	}
};
