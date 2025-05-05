import { z, ZodError, type ZodTypeAny } from 'zod';

type SvelteKitServerApiRequestDataBase<S extends ZodTypeAny> = {
	path: string;
	responseSchema: S;
};

type SvelteKitServerApiGetRequestData<S extends ZodTypeAny> =
	SvelteKitServerApiRequestDataBase<S> & {
		method: 'GET';
	};

type SvelteKitServerApiPostRequestData<S extends ZodTypeAny> =
	SvelteKitServerApiRequestDataBase<S> & {
		method: 'POST';
		body?: Record<string, unknown>;
	};

type SvelteKitServerApiRequestMetaData<S extends ZodTypeAny> =
	| SvelteKitServerApiGetRequestData<S>
	| SvelteKitServerApiPostRequestData<S>;

const errorResponseSchema = z.object({
	message: z.string()
});

export type SvelteKitServerApiResponse<S extends ZodTypeAny> = Promise<
	| {
			status: 'success';
			data: z.infer<S>;
	  }
	| {
			status: 'error';
			httpCode: number;
			message: string;
	  }
>;

export const makeRequestToServerApi = async <S extends ZodTypeAny>(
	reqMeta: SvelteKitServerApiRequestMetaData<S>
): SvelteKitServerApiResponse<S> => {
	const { path, method, responseSchema } = reqMeta;
	const url = `/api/${path}`;
	const res = await fetch(url, {
		method,
		headers: {
			'Content-Type': 'application/json'
		},
		body: reqMeta.method === 'POST' && reqMeta.body ? JSON.stringify(reqMeta.body) : undefined
	});

	const reponseIsJson = res.headers.get('content-type') === 'application/json';
	if (!res.ok) {
		if (!reponseIsJson) {
			const responseText = await res.text();
			return {
				status: 'error',
				httpCode: res.status,
				message: createErrorMessageForUI(
					`Request to server API failed with status ${res.status} and unexpected non-JSON response`,
					responseText
				)
			};
		}
		const responseJson = await res.json();
		const errorParseRes = errorResponseSchema.safeParse(responseJson);
		if (errorParseRes.success) {
			const { message } = errorParseRes.data;
			return {
				status: 'error',
				httpCode: res.status,
				message
			};
		} else {
			const jsonString = JSON.stringify(responseJson, null, 2);
			const errorDesc = `Request to server API failed with status ${res.status} and unexpected JSON response`;
			console.error(errorDesc, {
				responseJson,
				validationError: errorParseRes.error
			});
			return {
				status: 'error',
				httpCode: res.status,
				message: createErrorMessageForUI(errorDesc, jsonString)
			};
		}
	}

	if (!reponseIsJson) {
		const errorDesc = `Request to server API at ${url} returned non-JSON response`;
		const responseText = await res.text();
		console.error(`${errorDesc}\n${responseText}`);
		return {
			status: 'error',
			message: createErrorMessageForUI(errorDesc, responseText),
			httpCode: res.status
		};
	}
	const responseJson = await res.json();
	const schemaParseRes = responseSchema.safeParse(responseJson);
	if (!schemaParseRes.success) {
		const errorDesc = `Response from server API at ${url} did not match expected schema`;
		console.error(errorDesc, {
			validationError: schemaParseRes.error
		});
		return {
			status: 'error',
			message: errorDesc + '\n' + zodErrorToErrorMessage(schemaParseRes.error),
			httpCode: res.status
		};
	}
	return {
		status: 'success',
		data: schemaParseRes.data
	};
};

function createErrorMessageForUI(errorDesc: string, responseText: string, maxChars = 500) {
	const messageBody =
		responseText.length > maxChars
			? responseText.slice(0, maxChars) + '\n(check console for more...)'
			: responseText;
	return `${errorDesc}\n${messageBody}`;
}

function zodErrorToErrorMessage(e: ZodError): string {
	const maxVisible = 7;
	const messages = e.errors.slice(0, maxVisible).map((err) => {
		const path = parseTaskCreationZodValidationErrorPath(err.path);
		return `${path}: ${err.message}`;
	});

	if (e.errors.length > maxVisible) {
		messages.push(`... (${e.errors.length - maxVisible} more)`);
	}

	return messages.join('\n');
}

function parseTaskCreationZodValidationErrorPath(path: (string | number)[]) {
	if (path.length === 0) {
		return 'value';
	}
	if (path.length === 1) {
		return path[0];
	}
	return path.join('.');
}
