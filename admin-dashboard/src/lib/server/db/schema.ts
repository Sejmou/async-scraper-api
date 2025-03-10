import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';
import { createSelectSchema, createInsertSchema } from 'drizzle-zod';

export const server = sqliteTable('server', {
	id: integer('id').primaryKey(),
	protocol: text('protocol').notNull(),
	host: text('host').notNull(),
	port: integer('port').notNull(),
	addedAt: text('added_at')
		.default(sql`(CURRENT_TIMESTAMP)`)
		.notNull()
});

export const serverSelectSchema = createSelectSchema(server);
export const serverInsertSchema = createInsertSchema(server);
