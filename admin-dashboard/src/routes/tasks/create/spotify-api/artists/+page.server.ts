import { artistsPayloadSchema } from '$lib/scraper-types-and-schemas/new-tasks/spotify-api.js';
import { superValidate, message } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';

export const actions = {
	default: async (event) => {
		console.log(event);
		const form = await superValidate(event, zod(artistsPayloadSchema));
		if (!form.valid) {
			return message(form, {
				type: 'error',
				text: 'The data you provided is invalid'
			});
		}

		console.log(form);

		return { form };
	}
};
