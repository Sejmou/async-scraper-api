import { test, expect } from 'vitest';
import { roundRobinSplit } from './utils';

test('splits array into k chunks in order of importance', () => {
	expect(roundRobinSplit([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)).toStrictEqual([
		[1, 4, 7],
		[2, 5, 8],
		[3, 6, 9]
	]);
});
