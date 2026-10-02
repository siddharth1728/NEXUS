import { api } from './client';
import { Action, ActionEdge, ActionStatus } from './types';

export const actionsApi = {
  getActions: (params?: { skip?: number; limit?: number }) => 
    api.get<Action[]>(`/actions?skip=${params?.skip || 0}&limit=${params?.limit || 100}`),
  
  getAction: (id: string) => 
    api.get<Action>(`/actions/${id}`),

  createAction: (data: Partial<Action>) =>
    api.post<Action>('/actions', data),

  updateActionState: (id: string, new_status: ActionStatus) =>
    api.post<Action>(`/actions/${id}/state`, { new_status }),

  getActionEdges: (id: string) =>
    api.get<ActionEdge[]>(`/actions/${id}/edges`),
};
