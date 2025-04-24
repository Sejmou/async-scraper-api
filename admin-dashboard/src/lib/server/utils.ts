import { error } from '@sveltejs/kit';

export async function safeParseRequestJSON(request: Request) {
	try {
		const json = await request.json();
		return json as unknown;
	} catch (e) {
		console.error('Failed to parse request JSON', { request, error: e });
		error(400, 'Invalid JSON in request body');
	}
}
