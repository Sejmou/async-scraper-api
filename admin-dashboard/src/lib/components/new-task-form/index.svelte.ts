import { superForm, defaults, type SuperForm, type ValidationErrors } from 'sveltekit-superforms';
import { z } from 'zod';
import { zod } from 'sveltekit-superforms/adapters';
import { createTask } from '$lib/client-api/scraper-tasks';
import { goto } from '$app/navigation';
import type { SupportedTask } from '$lib/scraper-types-and-schemas/new-tasks';
import { get } from 'svelte/store';
import NewTaskForm from './new-task-form.svelte';

export { NewTaskForm };

export class TaskFormState<TaskType extends SupportedTask, ParamsType extends z.ZodSchema> {
	#form: SuperForm<z.infer<ParamsType>>;
	#inputs: TaskType['inputs'] = $state([]);
	#initialTaskValue: TaskType;

	constructor(initialTaskValue: TaskType, taskParamsSchema: ParamsType) {
		this.#initialTaskValue = structuredClone(initialTaskValue);
		this.#form = superForm(defaults(zod(taskParamsSchema)), {
			SPA: true,
			dataType: 'json',
			validators: zod(taskParamsSchema),
			resetForm: false
		});
	}

	get inputs() {
		return this.#inputs;
	}

	updateInputs(newInputs: TaskType['inputs']) {
		this.#inputs = newInputs;
	}

	get form() {
		return this.#form;
	}

	get formData() {
		return this.#form.form;
	}

	get message() {
		return this.#form.message;
	}

	get errors() {
		return this.#form.errors;
	}

	get enhance() {
		return this.#form.enhance;
	}

	async handleSubmit(event: Event) {
		event.preventDefault();
		const paramsValidationResult = await this.#form.validateForm();
		console.log({ paramsValidationResult });

		if (!paramsValidationResult.valid) {
			this.#form.errors.update((v) => {
				return {
					...v,
					...this.#extractParamsValidationErrors(paramsValidationResult.errors)
				};
			});
			return;
		}

		const task = this.#createTaskObjToSend();

		const res = await createTask(task);
		if (res.status === 'success') {
			await goto(`/tasks/${res.id}`);
		} else {
			this.#form.message.set({
				type: 'error',
				text: res.error
			});
		}
	}

	#extractParamsValidationErrors(errors: ValidationErrors<z.TypeOf<ParamsType>>) {
		const extractedErrors: Record<string, unknown> = {};
		for (const [key, value] of Object.entries(errors)) {
			extractedErrors[key] = value;
		}
		return extractedErrors;
	}

	#createTaskObjToSend() {
		// use initialTaskValue to figure out what type of task object to create at runtime
		const task = structuredClone(this.#initialTaskValue);
		task.inputs = this.#inputs;
		const formData = get(this.formData);
		if ('params' in task) {
			task.params = formData.params;
		}
		return task;
	}
}
