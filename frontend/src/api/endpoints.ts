import { api } from './client';
import { Document, ExecutionRequest } from './types';

export const documentsApi = {
  getDocuments: (params?: { skip?: number; limit?: number }) => 
    api.get<Document[]>(`/documents?skip=${params?.skip || 0}&limit=${params?.limit || 100}`),
  
  getDocument: (id: string) => 
    api.get<Document>(`/documents/${id}`),
};

export const executionsApi = {
  getExecutions: (params?: { skip?: number; limit?: number }) => 
    api.get<ExecutionRequest[]>(`/execution?skip=${params?.skip || 0}&limit=${params?.limit || 100}`),
  
  getExecution: (id: string) => 
    api.get<ExecutionRequest>(`/execution/${id}`),

  approveExecution: (id: string) =>
    api.post<ExecutionRequest>(`/execution/${id}/review`, { decision: 'APPROVED' }),

  rejectExecution: (id: string) =>
    api.post<ExecutionRequest>(`/execution/${id}/review`, { decision: 'REJECTED' }),
};
