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

export const taskTbl = sqliteTable('task', {
	id: integer('id').primaryKey(),
	dataSource: text('data_source').notNull(),
	taskType: text('task_type').notNull(),
	params: text('params', { mode: 'json' }),
	createdAt: text('created_at')
		.default(sql`(CURRENT_TIMESTAMP)`)
		.notNull()
});

export const taskSelectSchema = createSelectSchema(taskTbl);

// there's a bug(or maybe that's intended?) causing this to return type Json for params, but db.select(...) and db.query(...) return type unknown
// this is a hack to fix the inconsistency
type TaskSelect = z.infer<typeof taskSelectSchema>;
export type DBTask = Omit<TaskSelect, 'params'> & { params: unknown };

export const taskInsertSchema = createInsertSchema(taskTbl);
export type TaskInsert = z.infer<typeof taskInsertSchema>;

export const subtaskTbl = sqliteTable('subtask', {
	id: integer('id').primaryKey(),
	taskId: integer('task_id')
		.notNull()
		.references((): AnySQLiteColumn => taskTbl.id, { onDelete: 'cascade' }),
	scraperTaskId: integer('scraper_task_id').notNull(),
	scraperId: integer('scraper_id')
		.notNull()
		.references((): AnySQLiteColumn => scraperServerTbl.id, { onDelete: 'cascade' })
});

export const subtaskSelectSchema = createSelectSchema(subtaskTbl);
export type Subtask = z.infer<typeof subtaskSelectSchema>;
export const subtaskInsertSchema = createInsertSchema(subtaskTbl);
export type SubtaskInsert = z.infer<typeof subtaskInsertSchema>;

export const taskRelations = relations(taskTbl, ({ many }) => ({
	subtasks: many(subtaskTbl)
}));

export const subtaskRelations = relations(subtaskTbl, ({ one }) => ({
	task: one(taskTbl, {
		fields: [subtaskTbl.taskId],
		references: [taskTbl.id]
	}),
	scraper: one(scraperServerTbl, {
		fields: [subtaskTbl.scraperId],
		references: [scraperServerTbl.id]
	})
}));
