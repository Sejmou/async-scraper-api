import { sqliteTable, text, integer, unique } from 'drizzle-orm/sqlite-core';
import { relations, sql } from 'drizzle-orm';
import { createSelectSchema, createInsertSchema } from 'drizzle-zod';
import { z } from 'zod';

export const serverTbl = sqliteTable(
	'server',
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

export const serverSelectSchema = createSelectSchema(serverTbl);
export const serverInsertSchema = createInsertSchema(serverTbl);
export type ServerInsert = z.infer<typeof serverInsertSchema>;

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
export const taskInsertSchema = createInsertSchema(taskTbl);
export type TaskInsert = z.infer<typeof taskInsertSchema>;

export const subtaskTbl = sqliteTable('subtask', {
	id: integer('id').primaryKey(),
	taskId: integer('task_id').notNull(),
	scraperId: integer('scraper_id').notNull()
});

export const subtaskSelectSchema = createSelectSchema(subtaskTbl);
export const subtaskInsertSchema = createInsertSchema(subtaskTbl);
export type SubtaskInsert = z.infer<typeof subtaskInsertSchema>;

export const taskRelations = relations(taskTbl, ({ many }) => ({
	subtasks: many(subtaskTbl)
}));

export const subtaskRelations = relations(subtaskTbl, ({ one }) => ({
	task: one(taskTbl, {
		fields: [subtaskTbl.taskId],
		references: [taskTbl.id]
	})
}));
