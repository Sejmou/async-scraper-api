import { makeRequestToServerApi, type SvelteKitServerApiResponse } from '$lib/client-api';
import { subtaskActionResultSchema } from '$lib/types-and-schemas/distributed-tasks';


export type DistributedTaskSubtaskActionResponse = SvelteKitServerApiResponse<typeof subtaskActionResultSchema>;

export async function pauseDistributedTask(taskId: number): DistributedTaskSubtaskActionResponse {
  return await makeRequestToServerApi({
    method: 'POST',
    path: `tasks/${taskId}/pause`,
    responseSchema: subtaskActionResultSchema
  });
}

export async function executeDisctributedTask(taskId: number): DistributedTaskSubtaskActionResponse {
  return await makeRequestToServerApi({
    method: 'POST',
    path: `tasks/${taskId}/execute`,
    responseSchema: subtaskActionResultSchema
  });
}
