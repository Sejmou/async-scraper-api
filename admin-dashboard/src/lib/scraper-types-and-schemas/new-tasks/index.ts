export type Scraper = {
	host: string;
	port: number;
	protocol: string;
};

export type Task<T extends Record<string, unknown>> = {
	dataSource: string;
	taskType: string;
	payload: T;
};
