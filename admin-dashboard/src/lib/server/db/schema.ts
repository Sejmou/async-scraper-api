import { sqliteTable, text, integer, unique, type AnySQLiteColumn } from 'drizzle-orm/sqlite-core';
import { relations, sql } from 'drizzle-orm';
import { createSelectSchema, createInsertSchema } from 'drizzle-zod';
import { z } from 'zod';

export const scraperServerTbl = sqliteTable(
	'scraper_server',
	{
		id: integer('id').primaryKey(),
		protocol: text('protocol').notNull(),
		host: text('host').notNull(),
		port: integer('port').notNull(),
		addedAt: text('added_at')
			.default(sql`(CURRENT_TIMESTAMP)`)
			.notNull()
	},
	(t) => [unique().on(t.host, t.port)]
);

export const scraperSelectSchema = createSelectSchema(scraperServerTbl);
export type Scraper = z.infer<typeof scraperSelectSchema>;
export const scraperInsertSchema = createInsertSchema(scraperServerTbl);
export type ScraperInsert = z.infer<typeof scraperInsertSchema>;

export const distTaskTbl = sqliteTable('task', {
	id: integer('id').primaryKey(),
	dataSource: text('data_source').notNull(),
	taskType: text('task_type').notNull(),
	params: text('params', { mode: 'json' }),
	createdAt: text('created_at')
		.default(sql`(CURRENT_TIMESTAMP)`)
		.notNull()
});

export const distTaskSelectSchema = createSelectSchema(distTaskTbl);

// there's a bug(or maybe that's intended?) causing this to return type Json for params, but db.select(...) and db.query(...) return type unknown
// this is a hack to fix the inconsistency
type DistributedTaskSelect = z.infer<typeof distTaskSelectSchema>;
/**
 * A distributed task is a task that has been distributed across multiple scrapers.
 *
 * In a distributed task, each scraper instance is responsible for fetching data for a subset of the overall task inputs within a separate subtask. Each subtask shares the same data source and task type as well as parameters (if there are any).
 *
 * We can get all the subtasks that make up a distributed task by querying the subtask table with the task ID.
 */
export type DistributedTask = Omit<DistributedTaskSelect, 'params'> & { params: unknown };

export const distTaskInsertSchema = createInsertSchema(distTaskTbl);
export type DistributedTaskInsert = z.infer<typeof distTaskInsertSchema>;

export const subtaskTbl = sqliteTable('subtask', {
	id: integer('id').primaryKey(),
	taskId: integer('task_id')
		.notNull()
		.references((): AnySQLiteColumn => distTaskTbl.id, { onDelete: 'cascade' }),
	scraperTaskId: integer('scraper_task_id').notNull(),
	scraperId: integer('scraper_id')
		.notNull()
		.references((): AnySQLiteColumn => scraperServerTbl.id, { onDelete: 'cascade' })
});

export const subtaskSelectSchema = createSelectSchema(subtaskTbl);
export type Subtask = z.infer<typeof subtaskSelectSchema>;
export const subtaskInsertSchema = createInsertSchema(subtaskTbl);
export type SubtaskInsert = z.infer<typeof subtaskInsertSchema>;

export const distTaskRelations = relations(distTaskTbl, ({ many }) => ({
	subtasks: many(subtaskTbl)
}));

export const subtaskRelations = relations(subtaskTbl, ({ one }) => ({
	task: one(distTaskTbl, {
		fields: [subtaskTbl.taskId],
		references: [distTaskTbl.id]
	}),
	scraper: one(scraperServerTbl, {
		fields: [subtaskTbl.scraperId],
		references: [scraperServerTbl.id]
	})
}));
