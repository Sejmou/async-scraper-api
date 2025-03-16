import { sqliteTable, text, integer, unique } from 'drizzle-orm/sqlite-core';
import { relations, sql } from 'drizzle-orm';
import { createSelectSchema, createInsertSchema } from 'drizzle-zod';
import { z } from 'zod';

export const server = sqliteTable(
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

export const serverSelectSchema = createSelectSchema(server);
export const serverInsertSchema = createInsertSchema(server);
export type ServerInsert = z.infer<typeof serverInsertSchema>;

export const task = sqliteTable('task', {
	id: integer('id').primaryKey(),
	dataSource: text('data_source').notNull(),
	taskType: text('task_type').notNull(),
	params: text('params', { mode: 'json' }),
	createdAt: text('created_at')
		.default(sql`(CURRENT_TIMESTAMP)`)
		.notNull()
});

export const taskSelectSchema = createSelectSchema(task);
export const taskInsertSchema = createInsertSchema(task);
export type TaskInsert = z.infer<typeof taskInsertSchema>;

export const subtask = sqliteTable('subtask', {
	id: integer('id').primaryKey(),
	taskId: integer('task_id').notNull(),
	scraperId: integer('scraper_id').notNull()
});

export const subtaskSelectSchema = createSelectSchema(subtask);
export const subtaskInsertSchema = createInsertSchema(subtask);
export type SubtaskInsert = z.infer<typeof subtaskInsertSchema>;

export const taskRelations = relations(task, ({ many }) => ({
	subtasks: many(subtask)
}));

export const subtaskRelations = relations(subtask, ({ one }) => ({
	task: one(task, {
		fields: [subtask.taskId],
		references: [task.id]
	})
}));
