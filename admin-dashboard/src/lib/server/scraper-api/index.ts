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
	body?: Record<string, unknown> | unknown[];
};

type ScraperDeleteRequestData<S extends ZodTypeAny> = ScraperRequestDataBase<S> & {
	method: 'DELETE';
};

type ScraperRequestMetaData<S extends ZodTypeAny> =
	| ScraperGetRequestData<S>
	| ScraperPostRequestData<S>
	| ScraperDeleteRequestData<S>;

export const constructScraperBaseUrl = (scraper: Scraper): string => {
	return `${scraper.protocol}://${scraper.host}:${scraper.port}`;
};

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
	return `${constructScraperBaseUrl(scraper)}/${pathWithParams}`;
};

const errorResponseSchema = z.object({
	detail: z.string()
});

export const makeRequestToScraper = async <S extends ZodTypeAny>(
	reqMeta: ScraperRequestMetaData<S>
): Promise<
	| {
			status: 'success';
			data: z.infer<S>;
	  }
	| {
			status: 'error';
			httpCode: number;
			message: string;
	  }
> => {
	// separate out the responseSchema from the requestData
	const { responseSchema, ...requestData } = reqMeta;
	const { scraper, path, params, method } = requestData;
	const url = constructScraperRequestUrl(scraper, path, params);

	try {
		const res = await fetch(url, {
			method,
			headers: {
				'Content-Type': 'application/json'
			},
			body: reqMeta.method === 'POST' && reqMeta.body ? JSON.stringify(reqMeta.body) : undefined
		});
		const responseData = await res.json();
		if (!res.ok) {
			const errorParseRes = errorResponseSchema.safeParse(responseData);
			if (errorParseRes.success) {
				const { detail } = errorParseRes.data;
				return {
					status: 'error',
					httpCode: res.status,
					message: detail
				};
			} else {
				const message = `Unexpected response body (check server logs)`;
				console.error(message, {
					responseData,
					validationError: errorParseRes.error
				});
				return {
					status: 'error',
					httpCode: res.status,
					message
				};
			}
		}
		const schemaParseRes = responseSchema.safeParse(responseData);
		if (!schemaParseRes.success) {
			const message = `Response did not match expected schema`;
			console.error(message, {
				responseData,
				validationError: schemaParseRes.error
			});
			return {
				status: 'error',
				message,
				httpCode: res.status
			};
		}
		return {
			status: 'success',
			data: schemaParseRes.data
		};
	} catch (e) {
		if (
			e instanceof TypeError &&
			e.cause &&
			typeof e.cause === 'object' &&
			'code' in e.cause &&
			e.cause.code === 'ECONNREFUSED'
		) {
			const message = `Request could not be sent (scraper is probably offline)`;
			console.warn(message, {
				scraper,
				requestData
			});
			return {
				status: 'error',
				httpCode: 503,
				message
			};
		} else {
			const message = `Request failed (unexpected error, see server logs)`;
			console.error(message, {
				scraper,
				requestData,
				error: e
			});
			return {
				status: 'error',
				httpCode: 500,
				message
			};
		}
	}
};
