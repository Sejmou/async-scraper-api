import { pauseTask } from "$lib/server/scraper-api/tasks/state-management";
import { db } from "$lib/server/db";
import { error, json } from "@sveltejs/kit";

export async function POST({ params }) {
  const taskId = Number(params.taskId);
  if (Number.isNaN(taskId)) {
    error(400, 'Invalid taskId');
  }

  const taskWithSubtasksAndScrapers = await db.query.distTaskTbl.findFirst({where: (tasks, { eq }) => eq(tasks.id, taskId), with:{
    subtasks: {
      with: {
        scraper: true
      }
    }
  }});

  if (!taskWithSubtasksAndScrapers) {
    error(404, 'Task not found');
  }

  // scrapers and their local task IDs
  // every subtask has a different task ID, local to the scraper
  const scrapersAndLocalTaskIds = taskWithSubtasksAndScrapers.subtasks.map(subtask => ({
    scraper: subtask.scraper,
    taskId: subtask.scraperTaskId
  }));

  const resultsRaw = await Promise.all(
    scrapersAndLocalTaskIds.map(async ({ scraper, taskId }) => {
      const result = await pauseTask(scraper, taskId);
      if (result.status === 'success') {
        return {
          scraperId: scraper.id,
          status: 'success' as const
        }
      } else {
        return {
          scraperId: scraper.id,
          status: 'error' as const,
          reason: result.message
        }
      }
    }

  ));

  const successes: number[] = [];
  const errors: {
    scraperId: number;
    reason: string;
  }[] = [];

  for (const result of resultsRaw) {
    if (result.status === 'success') {
      successes.push(result.scraperId);
    } else {
      errors.push({
        scraperId: result.scraperId,
        reason: result.reason
      });
    }
  }

  const results = {
    successes,
    errors
  }

  return json(results)
}