import { tracksParamsSchema } from '$lib/scraper-types-and-schemas/new-tasks/spotify-api.js';
import { superValidate, message } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';

export async function load() {
	return {
		tracksForm: await superValidate(zod(tracksParamsSchema))
	};
}

export const actions = {
	default: async (event) => {
		const form = await superValidate(event, zod(tracksParamsSchema));
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
