import { browser } from '$app/environment';
import * as duckdb from '@duckdb/duckdb-wasm';
import { type JSONSerializableValue } from './utils';

export type DuckDB = {
	/**
	 * Creates a DuckDB table from the provided file.
	 *
	 * @param file A file to create a table from. All formats supported by DuckDB should work. Additionally, .txt files are converted to single-column CSV for the import process.
	 * @param tableName The name of the table to create.
	 * @returns A promise that resolves when the table has been created.
	 */
	createTableFromFile: (file: File, tableName: string) => Promise<void>;
	executeQuery: (query: string) => Promise<QueryOutputRowMajor>;
	getRowCount: (tableName: string) => Promise<number>;
	createTableFromJSON: (data: JSONSerializableValue[], tableName: string) => Promise<void>;
};
export type QueryOutputRowMajor = QueryResultRowMajor | QueryExecutionError;
export type QueryOutputColumnMajor = QueryResultColumnMajor | QueryExecutionError;

type QueryExecutionError = {
	type: 'error';
	message: string;
	error?: Error;
};
export type QueryResultRowMajor = {
	type: 'result';
	columns: string[];
	data: {
		[x: string]: JSONSerializableValue;
	}[];
};
export type QueryResultColumnMajor = {
	type: 'result';
	columns: string[];
	data: {
		[x: string]: JSONSerializableValue[];
	};
};

type DuckDBState =
	| {
			state: 'loading';
			progress: number;
	  }
	| {
			state: 'ready';
			db: DuckDB;
	  }
	| {
			state: 'error';
			error: Error;
	  };

let duckDB = $state<DuckDBState>({ state: 'loading', progress: 0 });

export function getDuckDB() {
	return {
		get value() {
			return duckDB;
		}
	};
}

/**
 * Creates a DuckDB instance in the browser.
 * Should NOT be called on the server (it doesn't make sense and will NOT work)
 */
const createDuckDB = async () => {
	const duckdb_wasm = (await import('@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url')).default;
	// follow same process for other imports
	const mvp_worker = (await import('@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url'))
		.default;
	const duckdb_wasm_eh = (await import('@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url')).default;
	const eh_worker = (await import('@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url'))
		.default;

	// create 'lookup' object for bundle selection
	// IIUC, 'manual' in this case means that we manually pick bundles from the current builds that are included in the project
	// instead of automatically selecting the bundles from a CDN (e.g. jsDelivr), but I'm not entirely sure
	const MANUAL_BUNDLES: duckdb.DuckDBBundles = {
		mvp: {
			mainModule: duckdb_wasm,
			mainWorker: mvp_worker
		},
		eh: {
			mainModule: duckdb_wasm_eh,
			mainWorker: eh_worker
		}
	};
	// Select a bundle based on browser checks
	const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);

	// Instantiate the asynchronus version of DuckDB-wasm
	const worker = new Worker(bundle.mainWorker!);
	const logger = new duckdb.ConsoleLogger();
	const db = new duckdb.AsyncDuckDB(logger, worker);

	return { db, bundle };
};

const handleInstantiationProgress = (progress: duckdb.InstantiationProgress) => {
	const { bytesLoaded, bytesTotal } = progress;
	const progressPercentage = bytesLoaded / bytesTotal;
	// console.log(`DuckDB instantiation progress: ${Math.round(progressPercentage * 100)}%`);
	duckDB = { state: 'loading', progress: progressPercentage };
};

// we can only create the DuckDB instance in the browser, on the server we don't have access to the Web Worker API
const { db: dbInternal, bundle } = browser
	? await createDuckDB()
	: {
			db: null as unknown as duckdb.AsyncDuckDB,
			bundle: null as unknown as duckdb.DuckDBBundle
		};

if (browser) {
	// similarly, we can only call the instantiate method in the browser
	dbInternal
		.instantiate(bundle.mainModule, bundle.pthreadWorker, handleInstantiationProgress)
		.then(() => {
			// console.log('DuckDB instance ready');
			duckDB = {
				state: 'ready',
				db: {
					createTableFromFile: async (
						file: File,
						tableName: string,
						first_csv_line_contains_headers = false
					) => {
						const fileName = file.name.endsWith('.txt') ? 'file.csv' : file.name;
						await dbInternal.dropFile(fileName);
						await dbInternal.registerFileHandle(
							fileName,
							file,
							duckdb.DuckDBDataProtocol.BROWSER_FILEREADER,
							true
						);

						const conn = await dbInternal.connect();
						await conn.query(`DROP TABLE IF EXISTS ${tableName}`);
						if (fileName.endsWith('.csv')) {
							conn.query(
								`CREATE TABLE ${tableName} AS SELECT * FROM read_csv('${fileName}', header=${first_csv_line_contains_headers})`
							);
						} else {
							await conn.query(`CREATE TABLE ${tableName} AS SELECT * FROM '${fileName}'`);
						}
						conn.close();
					},
					executeQuery: async (query: string) => executeQueryRowMajor(dbInternal, query),
					getRowCount: async (tableName: string) => {
						const res = await executeQueryRowMajor(
							dbInternal,
							`SELECT COUNT(*) AS count FROM ${tableName}`
						);
						if (res.type === 'result') {
							return Number(res.data[0]!.count);
						} else {
							throw Error(
								`Row count query for table ${tableName} failed. It probably does not exist!`
							);
						}
					},
					createTableFromJSON: async (data: JSONSerializableValue[], tableName: string) =>
						jsonArrayToTable(dbInternal, data, tableName)
				}
			};
		})
		.catch((error) => {
			console.error('Error instantiating DuckDB:', error);
			duckDB = { state: 'error', error };
		});
}

async function executeQueryColMajor(
	db: duckdb.AsyncDuckDB,
	query: string
): Promise<QueryOutputColumnMajor> {
	const c = await db.connect();
	try {
		// could type the result object(s) here if query were known statically
		// e.g. using c.query<{count: Int }>(...) instead of c.query(...) for query "SELECT COUNT(*) FROM ..."
		const resultTable = await c.query(query);
		const columns = resultTable.schema.fields.map((d) => d.name);
		const data: Record<string, JSONSerializableValue[]> = {};
		for (const col of columns) {
			data[col] = resultTable.getChild(col)!.toJSON();
		}
		const result: QueryResultColumnMajor = {
			type: 'result',
			columns,
			data
		};
		await c.close();
		return result;
	} catch (error) {
		await c.close();
		if (error instanceof Error) {
			console.error('Encountered Error while executing DuckDB query', error);
			return {
				type: 'error',
				message: error.message,
				error
			};
		} else {
			console.error('Encountered a non-Error type while executing DuckDB query:', error);
			return {
				type: 'error',
				message:
					'Something went wrong while executing the query in DuckDB. Check the browser console for details.'
			};
		}
	}
}

async function executeQueryRowMajor(
	db: duckdb.AsyncDuckDB,
	query: string
): Promise<QueryOutputRowMajor> {
	const result = await executeQueryColMajor(db, query);
	if (result.type === 'error') {
		return result;
	}
	const { columns, data: dataColMajor } = result;
	const data = colMajorToRowMajor(dataColMajor);
	return {
		type: 'result',
		columns,
		data
	};
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function colMajorToRowMajor<T extends Record<string, any[]>>(
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
 * Creates a new table in DuckDB from a JSON array.
 */
async function jsonArrayToTable(
	db: duckdb.AsyncDuckDB,
	data: JSONSerializableValue[],
	tableName: string
) {
	await db.registerFileText('rows.json', JSON.stringify(data));
	const c = await db.connect();
	await c.query(`DROP TABLE IF EXISTS ${tableName}`);
	await c.query(`CREATE TABLE ${tableName} AS SELECT * FROM 'rows.json'`);
	c.close();
}
