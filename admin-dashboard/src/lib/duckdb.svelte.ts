import { browser } from '$app/environment';
import * as duckdb from '@duckdb/duckdb-wasm';
import { colMajorToRowMajor, type JSONSerializableValue } from './utils';

/**
 * A custom high-level API for DuckDB.
 */
export class DuckDBAPI {
	#db: duckdb.AsyncDuckDB;

	constructor(db: duckdb.AsyncDuckDB) {
		this.#db = db;
	}

	/**
	 * Creates a DuckDB table from the provided file.
	 *
	 * @param file A file to create a table from. All formats supported by DuckDB should work. Additionally, .txt files are converted to single-column CSV for the import process.
	 * @param tableName The name of the table to create.
	 * @returns A promise that resolves when the table has been created.
	 */
	async createTableFromFile(
		file: File,
		tableName: string,
		first_csv_line_contains_headers = false
	) {
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
	}

	async executeQueryColMajor(query: string): Promise<QueryOutputColumnMajor> {
		const c = await this.#db.connect();
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

	async executeQueryRowMajor(query: string): Promise<QueryOutputRowMajor> {
		const result = await this.executeQueryColMajor(query);
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

	async getRowCount(tableName: string) {
		const res = await this.executeQueryRowMajor(`SELECT COUNT(*) AS count FROM ${tableName}`);
		if (res.type === 'result') {
			return Number(res.data[0]!.count);
		} else {
			throw Error(`Row count query for table ${tableName} failed. It probably does not exist!`);
		}
	}

	/**
	 * Creates a new table in DuckDB from a JSON array.
	 */
	async createArrayFromJSON(data: JSONSerializableValue[], tableName: string) {
		await this.#db.registerFileText('rows.json', JSON.stringify(data));
		const c = await this.#db.connect();
		await c.query(`DROP TABLE IF EXISTS ${tableName}`);
		await c.query(`CREATE TABLE ${tableName} AS SELECT * FROM 'rows.json'`);
		c.close();
	}
}

export type QueryOutputRowMajor = QueryResultRowMajor | QueryExecutionError;
export type QueryOutputColumnMajor = QueryResultColumnMajor | QueryExecutionError;

export type QueryExecutionError = {
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
			db: DuckDBAPI;
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
				db: new DuckDBAPI(dbInternal)
			};
		})
		.catch((error) => {
			console.error('Error instantiating DuckDB:', error);
			duckDB = { state: 'error', error };
		});
}
