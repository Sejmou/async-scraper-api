import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function truncate(input: string, maxLength: number) {
	if (input.length > maxLength) {
		return input.slice(0, maxLength - 3) + '...';
	}
	return input;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function colMajorToRowMajor<T extends Record<string, any[]>>(
	data: T
): Array<{ [K in keyof T]: T[K][number] }> {
	// make sure the record is not empty
	if (Object.keys(data).length === 0) {
		throw new Error('Record must not be empty');
	}

	// make sure the arrays are of equal length
	const lengths = Object.values(data).map((arr) => arr.length);
	if (lengths.some((l) => l !== lengths[0])) {
		throw new Error('Arrays in record must be of equal length');
	}

	// Get the length of the arrays (assuming all arrays have equal length)
	const length = Math.min(...Object.values(data).map((arr) => arr.length));

	// Create an array of objects by iterating over the arrays by index
	return Array.from({ length }, (_, i) => {
		// For each index `i`, build an object where each key corresponds to the ith element of the array
		return Object.keys(data).reduce(
			(acc, key) => {
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				(acc as any)[key] = data[key]![i];
				return acc;
			},
			{} as { [K in keyof T]: T[K][number] }
		);
	});
}

/**
 * Splits an array into k chunks using round-robin partitioning.
 * @param items - The array of items, ordered by importance (most important first).
 * @param  k - The number of chunks.
 * @returns An array containing k chunks. Within each chunk, the items are ordered by importance.
 */
export function roundRobinSplit<T>(items: T[], k: number): T[][] {
	const chunks: T[][] = Array.from({ length: k }, () => []);
	for (let i = 0; i < items.length; i++) {
		chunks[i % k].push(items[i]);
	}

	return chunks;
}

export type JSONSerializableValue =
	| string
	| number
	| boolean
	| null
	| JSONSerializableValue[]
	| JSONSerializableObject;
type JSONSerializableObject = { [key: string]: JSONSerializableValue };
