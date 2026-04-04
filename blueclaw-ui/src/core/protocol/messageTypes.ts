/**
 * messageTypes.ts - Blueclaw 消息协议定义（TypeScript版）
 * 
 * 协议版本: 1.0.0
 * 与后端 blueclaw/api/message_protocol.py 保持同步
 */

// 协议版本
export const PROTOCOL_VERSION = '1.0.0';

// ==================== 枚举类型 ====================

export enum MessageType {
  // Client -> Server
  TASK_START = 'task.start',
  THINKING_SELECT_OPTION = 'thinking.select_option',
  THINKING_CUSTOM_INPUT = 'thinking.custom_input',
  THINKING_CONFIRM_EXECUTION = 'thinking.confirm_execution',
  EXECUTION_INTERVENE = 'execution.intervene',
  EXECUTION_PAUSE = 'execution.pause',
  EXECUTION_RESUME = 'execution.resume',
  
  // Server -> Client
  THINKING_NODE_CREATED = 'thinking.node_created',
  THINKING_NODE_SELECTED = 'thinking.node_selected',
  EXECUTION_BLUEPRINT_LOADED = 'execution.blueprint_loaded',
  EXECUTION_STEP_STARTED = 'execution.step_started',
  EXECUTION_STEP_COMPLETED = 'execution.step_completed',
  EXECUTION_STEP_FAILED = 'execution.step_failed',
  EXECUTION_INTERVENTION_NEEDED = 'execution.intervention_needed',
  EXECUTION_REPLANNED = 'execution.replanned',
  EXECUTION_COMPLETED = 'execution.completed',
  
  // System
  ERROR = 'system.error',
  PING = 'system.ping',
  PONG = 'system.pong',
  CONNECTED = 'system.connected',
  DISCONNECTED = 'system.disconnected',
}

export enum NodeStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SELECTED = 'selected',
  SKIPPED = 'skipped',
}

export enum Phase {
  IDLE = 'idle',
  THINKING = 'thinking',
  EXECUTING = 'executing',
  INTERVENING = 'intervening',
  COMPLETED = 'completed',
}

// ==================== 数据接口 ====================

export interface BlueclawMessage {
  version: string;
  type: MessageType | string;
  payload: unknown;
  timestamp: number;
  message_id: string;
}

export interface ThinkingOptionData {
  id: string;
  label: string;
  description: string;
  confidence: number;
  is_default?: boolean;
}

export interface NodeMetadata {
  created_at?: number;
  version?: string;
  [key: string]: unknown;
}

export interface BlueprintNodeData {
  id: string;
  type: 'thinking' | 'execution';
  status: NodeStatus | string;
  metadata: NodeMetadata;
}

export interface ThinkingNodeData extends BlueprintNodeData {
  type: 'thinking';
  question: string;
  options: ThinkingOptionData[];
  selected_option?: string;
  custom_input?: string;
}

export interface ExecutionStepData extends BlueprintNodeData {
  type: 'execution';
  name: string;
  description: string;
  dependencies: string[];
  result?: unknown;
  error?: string;
  duration_ms?: number;
}

export interface InterventionActionData {
  type: string; // 'replan', 'skip', 'stop', 'retry'
  label: string;
  description: string;
}

export interface EngineStateData {
  phase: Phase | string;
  current_node_id: string | null;
  current_step_id: string | null;
  progress: number;
  status_message: string;
}

// ==================== Payload 类型 ====================

export interface TaskStartPayload {
  user_input: string;
  context?: Record<string, unknown>;
}

export interface SelectOptionPayload {
  node_id: string;
  option_id: string;
}

export interface CustomInputPayload {
  node_id: string;
  custom_input: string;
}

export interface ConfirmExecutionPayload {
  confirmed: boolean;
}

export interface IntervenePayload {
  step_id: string;
  action_type: string;
  custom_input?: string;
}

export interface ExecutionStepStartedPayload {
  step_id: string;
  step_name: string;
  index: number;
}

export interface ExecutionStepCompletedPayload {
  step_id: string;
  result?: unknown;
  duration_ms: number;
}

export interface ExecutionStepFailedPayload {
  step_id: string;
  error: string;
}

export interface ExecutionInterventionNeededPayload {
  step_id: string;
  step_name: string;
  reason: string;
  actions: InterventionActionData[];
}

export interface ExecutionCompletedPayload {
  success: boolean;
  summary: string;
  [key: string]: unknown;
}

export interface ExecutionReplannedPayload {
  step_id: string;
  new_steps: ExecutionStepData[];
  message: string;
}

export interface ErrorPayload {
  error_code: string;
  error_message: string;
  details?: Record<string, unknown>;
}

export interface ConnectedPayload {
  session_id: string;
  protocol_version: string;
  server_info: {
    name: string;
    version: string;
  };
}

// ==================== 消息工厂 ====================

export class MessageFactory {
  private static generateId(): string {
    return Math.random().toString(36).substring(2, 10);
  }

  static createTaskStart(userInput: string, context?: Record<string, unknown>): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.TASK_START,
      payload: { user_input: userInput, context } as TaskStartPayload,
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createSelectOption(nodeId: string, optionId: string): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.THINKING_SELECT_OPTION,
      payload: { node_id: nodeId, option_id: optionId } as SelectOptionPayload,
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createCustomInput(nodeId: string, customInput: string): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.THINKING_CUSTOM_INPUT,
      payload: { node_id: nodeId, custom_input: customInput } as CustomInputPayload,
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createConfirmExecution(confirmed: boolean): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.THINKING_CONFIRM_EXECUTION,
      payload: { confirmed } as ConfirmExecutionPayload,
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createIntervene(stepId: string, actionType: string, customInput?: string): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.EXECUTION_INTERVENE,
      payload: { step_id: stepId, action_type: actionType, custom_input: customInput } as IntervenePayload,
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createPause(): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.EXECUTION_PAUSE,
      payload: {},
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createResume(): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.EXECUTION_RESUME,
      payload: {},
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createPing(): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.PING,
      payload: {},
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }

  static createPong(): BlueclawMessage {
    return {
      version: PROTOCOL_VERSION,
      type: MessageType.PONG,
      payload: {},
      timestamp: Date.now(),
      message_id: this.generateId(),
    };
  }
}

// ==================== 版本兼容性检查 ====================

export interface VersionCompatibility {
  compatible: boolean;
  message: string;
  server_version: string;
}

export function checkVersionCompatibility(clientVersion: string): VersionCompatibility {
  const serverVersion = PROTOCOL_VERSION;
  const clientParts = clientVersion.split('.');
  const serverParts = serverVersion.split('.');

  // 主版本号必须相同
  if (clientParts[0] !== serverParts[0]) {
    return {
      compatible: false,
      message: `版本不兼容: 客户端 v${clientVersion}, 服务端 v${serverVersion}`,
      server_version: serverVersion,
    };
  }

  // 次版本号客户端可以低于服务端
  if (parseInt(clientParts[1]) > parseInt(serverParts[1])) {
    return {
      compatible: false,
      message: `客户端版本 v${clientVersion} 高于服务端 v${serverVersion}`,
      server_version: serverVersion,
    };
  }

  return {
    compatible: true,
    message: `版本兼容: v${clientVersion}`,
    server_version: serverVersion,
  };
}

// ==================== 工具函数 ====================

export function parseMessage(data: string): BlueclawMessage {
  const parsed = JSON.parse(data);
  return {
    version: parsed.version || PROTOCOL_VERSION,
    type: parsed.type as MessageType,
    payload: parsed.payload || {},
    timestamp: parsed.timestamp || Date.now(),
    message_id: parsed.message_id || MessageFactory['generateId'](),
  };
}

export function stringifyMessage(message: BlueclawMessage): string {
  return JSON.stringify(message);
}
