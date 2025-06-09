// src/types.ts

export type AgentActionType =
    | 'command'
    | 'file_operation'
    | 'file_save'
    | 'file_read'
    | 'file_list'
    | 'search'
    | 'web_scrape'
    | 'tool_call'
    | 'orchestrator_tool'
    | 'delegated_task'
    | 'thought'
    | 'code_execution';

export interface AgentAction {
  id: string;
  type: AgentActionType;
  prefix: string; // e.g., "Delegated to ResearchAgent", "Tool: some_actual_tool"
  detail: string; // e.g., The task_description for the member, or actual tool args
  status?: 'running' | 'success' | 'error' | 'pending';
  originalToolName?: string; // To store 'atransfer_task_to_member' if needed
  memberAgentId?: string;
}

export interface UserMessageData {
  id: string;
  sender: 'user';
  text: string;
  timestamp: Date;
}

export interface TaskStepData {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'success' | 'error' |"stopped";
  isActive?: boolean;
  agentActions?: AgentAction[];
  // New fields for controlling UI behavior of this step
  stepIconType?: AgentActionType | 'default_step_type' | string; // Allow string for flexibility from backend
  hideSubActions?: boolean;
}

export interface AgentMessageData {
  id: string;
  sender: 'agent';
  text?: string;
  task?: {
    title: string; // Overall task title (e.g., from user input or a plan summary)
    statusIcon?: 'loader' | 'check' | 'error'; // Overall task status
    isCollapsible?: boolean;
    isCollapsed?: boolean;
    steps: TaskStepData[];
    currentStepIndex?: number; // To easily find the active step
    totalSteps?: number; // From plan_ready
  };
  codeBlock?: {
    language: string;
    content: string;
  };
  timestamp: Date;
}

export type MessageData = UserMessageData | AgentMessageData;

export interface Session {
  id: string;
  name: string;
  active: boolean;
  status?: 'active' | 'completed' | 'error' | 'pending';
}

export interface Artifact {
  filename: string;
  type: 'markdown' | 'text' | 'image' | 'pdf' | 'json' | 'html' | 'unknown' | string;
  description?: string;
  url?: string;
  content?: string;
}