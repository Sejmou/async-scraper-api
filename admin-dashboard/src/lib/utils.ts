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

/**
 * Converts a number of bytes into a human-readable string.
 * @param bytes - The number of bytes.
 * @returns A string representing the size in human-readable format.
 */
export function humanReadableSize(bytes: number): string {
	if (bytes === 0) return '0 B';

	const units: string[] = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
	const i: number = Math.floor(Math.log(bytes) / Math.log(1024));
	const size: number = bytes / Math.pow(1024, i);

	return `${size.toFixed(2)} ${units[i]}`;
}

export type JSONSerializableValue =
	| string
	| number
	| boolean
	| null
	| JSONSerializableValue[]
	| JSONSerializableObject;
type JSONSerializableObject = { [key: string]: JSONSerializableValue };

/**
 * Helper type to make IDE hints for expected type (e.g. IntelliSense) easier to read
 *
 * Details (and code source): https://stackoverflow.com/a/57683652/13727176
 */
export type ExpandRecursively<T> = T extends object
	? T extends infer O
		? { [K in keyof O]: ExpandRecursively<O[K]> }
		: never
	: T;
