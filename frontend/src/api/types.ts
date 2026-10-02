// ENUMS
export enum ActionStatus {
  CANDIDATE = 'CANDIDATE',
  BLOCKED = 'BLOCKED',
  READY = 'READY',
  IN_PROGRESS = 'IN_PROGRESS',
  PENDING_VERIFICATION = 'PENDING_VERIFICATION',
  COMPLETED = 'COMPLETED',
  VERIFIED = 'VERIFIED',
  NOT_VERIFIED = 'NOT_VERIFIED',
  REJECTED = 'REJECTED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
  REQUIRES_REVIEW = 'REQUIRES_REVIEW',
}

export enum ConfidenceLevel {
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  REQUIRES_REVIEW = 'REQUIRES_REVIEW',
  UNKNOWN = 'UNKNOWN',
  CONFLICT = 'CONFLICT',
}

export enum EdgeRelationType {
  DEPENDS_ON = 'depends_on',
  CREATES = 'creates',
  APPLIES_TO = 'applies_to',
  ASSERTS = 'asserts',
  REQUIRES = 'requires',
  DUE_ON = 'due_on',
  COMPLETED_BY = 'completed_by',
  BLOCKS = 'blocks',
  SUPERSEDES = 'supersedes',
}

export enum ExecutionState {
  PENDING = 'PENDING',
  AUTHORIZED = 'AUTHORIZED',
  AWAITING_APPROVAL = 'AWAITING_APPROVAL',
  RUNNING = 'RUNNING',
  SUCCEEDED = 'SUCCEEDED',
  FAILED = 'FAILED',
  DENIED = 'DENIED',
  REJECTED = 'REJECTED',
}

export enum ExtractionJobStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  RETRYING = 'RETRYING',
}

// MODELS
export interface Action {
  id: string;
  tenant_id: string;
  title: string;
  description: string;
  priority: string;
  due_date: string | null;
  is_hard_deadline: boolean;
  assignee_id: string | null;
  confidence: ConfidenceLevel;
  status: ActionStatus;
  source_document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ActionEdge {
  id: string;
  tenant_id: string;
  source_id: string;
  target_id: string;
  relation_type: EdgeRelationType;
  metadata_payload: Record<string, any>;
  created_at: string;
}

export interface Document {
  id: string;
  tenant_id: string;
  filename: string;
  mime_type: string;
  content_hash: string;
  storage_path: string;
  size_bytes: number;
  metadata_payload: Record<string, any>;
  created_at: string;
}

export interface ExecutionRequest {
  id: string;
  tenant_id: string;
  action_id: string;
  tool_name: string;
  connector_name: string;
  parameters: Record<string, any>;
  state: ExecutionState;
  result_payload: Record<string, any> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface EvidenceRequirement {
  id: string;
  action_id: string;
  tool_id: string;
  parameters: Record<string, any>;
  expected_state: Record<string, any>;
  created_at: string;
}

export interface VerificationResult {
  is_verified: boolean;
  evidence_id: string | null;
}
