import { db } from '$lib/server/db';
import { eq } from 'drizzle-orm';
import { taskTbl } from '$lib/server/db/schema';

export const load = async ({ params }) => {
	const task = params.taskId
		? (await db.select().from(taskTbl).where(eq(taskTbl.id, +params.taskId)))[0]
		: null;

	return {
		task
	};
};
