import Root from './root.svelte';
import { z } from 'zod';

type TSchema = z.ZodSchema;

export type InputExtractorProps<T extends TSchema> = {
	inputsDescription: string;
	inputSchema: T;
	exampleInput: z.infer<T>;
	/**
	 * The name of the DuckDB table which the task inputs should temporarily be stored in before passing them to the scrapers.
	 */
	inputsTableName: string;
	onInputsAdded: (inputs: z.infer<T>[]) => void;
};

/**
 * A class to hold all the state for a particular instance of an input extractor that can be shared between subcomponents.
 *
 * Having all the state in this object saves us from having to pass down specific props separately. Instead, every subcomponent simply accepts an instance of this class as a prop.
 *
 * CAUTION: The object should only be created in the root component! All other components should receive the created state instance as a prop.
 */
export class InputExtractorState<T extends TSchema> {
	#inputs: z.infer<TSchema>[] = $state([]);
	#inputsTableHasData = $state(false);
	#props: InputExtractorProps<T>;

	constructor(props: InputExtractorProps<T>) {
		this.#props = props;
	}

	get inputs() {
		return this.#inputs;
	}

	set inputs(inputs: z.infer<TSchema>[]) {
		this.#inputs = inputs;
		this.#props.onInputsAdded(inputs);
	}

	get inputsTableHasData() {
		return this.#inputsTableHasData;
	}
	set inputsTableHasData(hasData: boolean) {
		this.#inputsTableHasData = hasData;
	}

	get inputsTableName() {
		return this.#props.inputsTableName;
	}

	get inputSchema() {
		return this.#props.inputSchema;
	}

	get exampleInput() {
		return this.#props.exampleInput;
	}

	get inputDescription() {
		return this.#props.inputsDescription;
	}
}

export { Root, Root as InputExtractor };
