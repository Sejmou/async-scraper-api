import { db } from '$lib/server/db';
import { error, json } from '@sveltejs/kit';

export async function GET({params}) {
  const taskId = Number(params.taskId);
    if (Number.isNaN(taskId)) {
      error(400, 'Invalid taskId');
    }
  
    const task = await db.query.distTaskTbl.findFirst({
      where: (t, { eq }) => eq(t.id, taskId),
      with: {
        subtasks: {
          with: {
            scraper: true
          }
        }
      }
    });
  
    if (!task) {
      error(404, 'Task not found');
    }

    return json(task);
}