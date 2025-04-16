import { superForm, defaults, type SuperForm, type ValidationErrors } from 'sveltekit-superforms';
import { z } from 'zod';
import { zod } from 'sveltekit-superforms/adapters';
import { createTask } from '$lib/client-api/scraper-tasks';
import { goto } from '$app/navigation';
import type { SupportedTask, TaskInputMeta } from '$lib/scraper-types-and-schemas/new-tasks';
import { get } from 'svelte/store';
import NewTaskForm from './new-task-form.svelte';
import { getContext, setContext } from 'svelte';
import type { Scraper } from '$lib/server/db/schema';

export { NewTaskForm };

class TaskFormState<TaskType extends SupportedTask, ParamsType extends z.ZodSchema> {
	#form: SuperForm<z.infer<ParamsType>>;
	#scrapers: Scraper[];
	#selectedScraperIds: number[] = $state([]);
	#inputs: TaskType['inputs'] = $state([]);
	#initialTaskValue: TaskType;
	#paramsSchema: ParamsType;
	#inputMeta: TaskInputMeta<TaskType['inputs'][0]>;

	constructor(
		scrapers: Scraper[],
		initialTaskValue: TaskType,
		taskParamsSchema: ParamsType,
		taskInputMeta: TaskInputMeta<TaskType['inputs'][0]>
	) {
		this.#scrapers = scrapers;
		this.#initialTaskValue = structuredClone(initialTaskValue);
		this.#paramsSchema = taskParamsSchema;
		this.#inputMeta = taskInputMeta;
		this.#form = superForm(defaults(zod(taskParamsSchema)), {
			SPA: true,
			dataType: 'json',
			validators: zod(taskParamsSchema),
			resetForm: false,
			// don't fully understand why, but if this is set to true, custom errors I set by updating #form.message if validation fails on the server are immediately cleared
			invalidateAll: false
		});
	}

	get inputs() {
		return this.#inputs;
	}

	get availableScrapers() {
		return this.#scrapers;
	}

	get selectedScraperIds() {
		return this.#selectedScraperIds;
	}

	set selectedScraperIds(newIds: number[]) {
		this.#selectedScraperIds = newIds;
	}

	updateInputs(newInputs: TaskType['inputs']) {
		// reset message (there could be leftover input errors from previous server-side validation)
		this.#form.message.set(undefined);
		this.#inputs = newInputs;
	}

	resetInputs() {
		this.#inputs = [];
	}

	get paramsSchema() {
		return this.#paramsSchema;
	}

	get inputMeta() {
		return this.#inputMeta;
	}

	get initialTaskValue() {
		return this.#initialTaskValue;
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

		const res = await createTask(task, this.selectedScraperIds);
		if (res.status === 'success') {
			await goto(`/tasks/${res.id}`);
		} else {
			console.error('Error while creating task', res.error);
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
			task.params = formData;
		}
		return task;
	}
}

const STATE_KEY = Symbol('TaskFormState');

export function setTaskFormState<T extends SupportedTask, P extends z.ZodSchema>(
	scrapers: Scraper[],
	initialTaskValue: T,
	taskParamsSchema: P,
	taskInputMeta: TaskInputMeta<T['inputs'][0]>
) {
	return setContext(
		STATE_KEY,
		new TaskFormState(scrapers, initialTaskValue, taskParamsSchema, taskInputMeta)
	);
}

export function getTaskFormState() {
	return getContext<ReturnType<typeof setTaskFormState>>(STATE_KEY);
}
