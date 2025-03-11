import { sqliteTable, text, integer, unique } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';
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
