import { type Scraper as Scraper } from '$lib/server/db/schema';

export const makeRequestToScraper = async (
	scraper: Scraper,
	path: string,
	payload?: Record<string, unknown>,
	params?: Record<string, string | number | boolean>
): Promise<
	| {
			status: 'success';
			data: Record<string, unknown>;
	  }
	| {
			status: 'error';
			error: Record<string, unknown>;
	  }
> => {
	const queryString = params
		? '?' +
			Object.entries(params)
				.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
				.join('&')
		: '';
	const pathWithParams = path + queryString;
	const url = `${scraper.protocol}://${scraper.host}:${scraper.port}/${pathWithParams}`;
	const res = await fetch(url, {
		method: payload ? 'POST' : 'GET',
		headers: {
			'Content-Type': 'application/json'
		},
		body: payload ? JSON.stringify(payload) : undefined
	});
	const data = await res.json();
	if (!res.ok) {
		console.error(`Request to scraper API at ${url} failed`, data);
		return {
			status: 'error',
			error: data
		};
	}
	return {
		status: 'success',
		data
	};
};
