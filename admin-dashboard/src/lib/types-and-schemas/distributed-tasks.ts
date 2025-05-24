import { z } from "zod";

/**
 * Schema for the result of a subtask action (at the time of this writing only pause and execute) on a distributed task.
 */
export const subtaskActionResultSchema = z.object({
  successes: z.array(z.number()),
  errors: z.array(
    z.object({
      scraperId: z.number(),
      reason: z.string(),
    })
  ),
});