import { superValidate, message } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import { tracksPayloadSchema } from '$lib/scraper-task-schemas/spotify-api';

export async function load() {
	return {
		tracksPayloadForm: await superValidate(zod(tracksPayloadSchema))
	};
}

export const actions = {
	default: async (event) => {
		const form = await superValidate(event, zod(tracksPayloadSchema));
		if (!form.valid) {
			return message(form, {
				type: 'error',
				text: 'The data you provided is invalid'
			});
		}

		return { form };
	}
};
