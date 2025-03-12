import { superValidate, message } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import { artistsPayloadSchema } from '$lib/scraper-task-schemas/spotify-api';

export async function load() {
	return {
		artistsPayloadForm: await superValidate(zod(artistsPayloadSchema))
	};
}

export const actions = {
	default: async (event) => {
		const form = await superValidate(event, zod(artistsPayloadSchema));
		if (!form.valid) {
			return message(form, {
				type: 'error',
				text: 'The data you provided is invalid'
			});
		}

		return { form };
	}
};
