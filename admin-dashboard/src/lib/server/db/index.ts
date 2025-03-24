import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';
import Database from 'better-sqlite3';
import { env } from '$env/dynamic/private';
import { sql } from 'drizzle-orm';
if (!env.DATABASE_URL) throw new Error('DATABASE_URL is not set');

const client = new Database(env.DATABASE_URL);
// workaround for broken SQLite3 transactions, adapted from: https://github.com/drizzle-team/drizzle-orm/issues/1723#issuecomment-1950721628
// TODO: remove once issue has been fixed
export const db = drizzle(client, { schema });
type Database = ReturnType<typeof drizzle>;
type Transaction = {
	readonly db: Database;
	readonly nestedIndex: number;
	readonly savepointName: string;
	transaction: <T>(tx: (t: Transaction) => Promise<T>) => Promise<T>;
	rollback: () => void;
};

export function createTransaction(
	db: Database,
	nestedIndex?: number,
	savepointName?: string
): Transaction {
	const idx = nestedIndex ?? 0;
	const name = savepointName ?? 'sp0';

	return {
		db,
		nestedIndex: idx,
		savepointName: name,
		transaction: async (tx) => {
			db.run(sql.raw(`savepoint ${name}`));
			const t = createTransaction(db, idx + 1, `sp${idx + 1}`);

			try {
				const txResult = await tx(t);
				db.run(sql.raw(`release savepoint ${name}`));
				return txResult;
			} catch (e) {
				db.run(sql.raw(`rollback to savepoint ${name}`));
				throw e;
			}
		},
		rollback: () => {
			throw new Error('Rollback called.  Reverting transaction');
		}
	};
}
