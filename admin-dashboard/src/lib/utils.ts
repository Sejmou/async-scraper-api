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

export type JSONSerializableValue =
	| string
	| number
	| boolean
	| null
	| JSONSerializableValue[]
	| JSONSerializableObject;
type JSONSerializableObject = { [key: string]: JSONSerializableValue };
