/**
 * BlueclawEngine.ts - 引擎客户端
 * 
 * 管理与后端的WebSocket通信
 * 处理消息收发、状态同步、重连逻辑
 */

import {
  BlueclawMessage,
  MessageType,
  MessageFactory,
  parseMessage,
  ThinkingNodeData,
  ExecutionStepData,
  InterventionActionData,
  EngineStateData,
  Phase,
  ConnectedPayload,
  ErrorPayload,
} from '../protocol/messageTypes';

// ==================== 事件类型 ====================

export interface EngineEvents {
  onConnect: (sessionId: string) => void;
  onDisconnect: (reason: string) => void;
  onError: (error: ErrorPayload) => void;
  
  // 思考阶段事件
  onThinkingNodeCreated: (node: ThinkingNodeData) => void;
  onOptionSelected: (nodeId: string, optionId: string) => void;
  
  // 执行阶段事件
  onBlueprintLoaded: (steps: ExecutionStepData[]) => void;
  onStepStarted: (stepId: string, stepName: string, index: number) => void;
  onStepCompleted: (stepId: string, result: unknown, durationMs: number) => void;
  onStepFailed: (stepId: string, error: string) => void;
  onExecutionCompleted: (success: boolean, summary: string) => void;
  
  // 干预事件
  onInterventionNeeded: (stepId: string, reason: string, actions: InterventionActionData[]) => void;
  onReplanned: (stepId: string, newSteps: ExecutionStepData[]) => void;
  
  // 状态事件
  onStateChanged: (state: EngineStateData) => void;
  onMessage: (message: string) => void;
}

export type PartialEngineEvents = Partial<EngineEvents>;

// ==================== 配置选项 ====================

export interface EngineConfig {
  wsUrl: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

const DEFAULT_CONFIG: Partial<EngineConfig> = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  pingInterval: 30000,
};

// ==================== 引擎客户端 ====================

export class BlueclawEngine {
  private ws: WebSocket | null = null;
  private config: EngineConfig;
  private events: PartialEngineEvents;
  
  // 状态
  private connected = false;
  private sessionId: string | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  
  // 消息队列（连接断开时暂存）
  private messageQueue: BlueclawMessage[] = [];

  constructor(config: EngineConfig, events: PartialEngineEvents = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.events = events;
  }

  // ============ 连接管理 ============

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.connected) {
        resolve();
        return;
      }

      try {
        this.ws = new WebSocket(this.config.wsUrl);

        this.ws.onopen = () => {
          console.log('[Engine] WebSocket connected');
          this.connected = true;
          this.reconnectAttempts = 0;
          this.startPing();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onclose = (event) => {
          console.log('[Engine] WebSocket closed:', event.code, event.reason);
          this.connected = false;
          this.sessionId = null;
          this.stopPing();
          
          if (this.events.onDisconnect) {
            this.events.onDisconnect(event.reason || 'Connection closed');
          }

          // 自动重连
          if (this.reconnectAttempts < (this.config.maxReconnectAttempts || 5)) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('[Engine] WebSocket error:', error);
          reject(new Error('WebSocket connection failed'));
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.stopReconnect();
    this.stopPing();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.connected = false;
    this.sessionId = null;
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;

    this.reconnectAttempts++;
    console.log(`[Engine] Reconnecting... (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch(() => {
        // 重连失败，继续尝试
      });
    }, this.config.reconnectInterval);
  }

  private stopReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // ============ Ping/Pong ============

  private startPing(): void {
    this.stopPing();
    this.pingTimer = setInterval(() => {
      if (this.connected) {
        this.send(MessageFactory.createPing());
      }
    }, this.config.pingInterval);
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  // ============ 消息处理 ============

  private handleMessage(data: string): void {
    try {
      const message = parseMessage(data);
      console.log('[Engine] Received:', message.type);

      switch (message.type) {
        case MessageType.CONNECTED:
          this.handleConnected(message.payload as ConnectedPayload);
          break;

        case MessageType.THINKING_NODE_CREATED:
          this.handleThinkingNodeCreated(message.payload as ThinkingNodeData);
          break;

        case MessageType.THINKING_NODE_SELECTED:
          // 由前端状态管理处理
          break;

        case MessageType.EXECUTION_BLUEPRINT_LOADED:
          this.handleBlueprintLoaded(message.payload as { steps: ExecutionStepData[] });
          break;

        case MessageType.EXECUTION_STEP_STARTED:
          this.handleStepStarted(message.payload as { step_id: string; step_name: string; index: number });
          break;

        case MessageType.EXECUTION_STEP_COMPLETED:
          this.handleStepCompleted(message.payload as { step_id: string; result: unknown; duration_ms: number });
          break;

        case MessageType.EXECUTION_STEP_FAILED:
          this.handleStepFailed(message.payload as { step_id: string; error: string });
          break;

        case MessageType.EXECUTION_INTERVENTION_NEEDED:
          this.handleInterventionNeeded(message.payload as { step_id: string; step_name: string; reason: string; actions: InterventionActionData[] });
          break;

        case MessageType.EXECUTION_REPLANNED:
          this.handleReplanned(message.payload as { step_id: string; new_steps: ExecutionStepData[] });
          break;

        case MessageType.EXECUTION_COMPLETED:
          this.handleExecutionCompleted(message.payload as { success: boolean; summary: string });
          break;

        case MessageType.ERROR:
          this.handleError(message.payload as ErrorPayload);
          break;

        case MessageType.PONG:
          // 心跳响应，无需处理
          break;

        default:
          console.log('[Engine] Unhandled message type:', message.type);
      }
    } catch (error) {
      console.error('[Engine] Failed to parse message:', error);
    }
  }

  // ============ 具体消息处理器 ============

  private handleConnected(payload: ConnectedPayload): void {
    this.sessionId = payload.session_id;
    console.log('[Engine] Session established:', this.sessionId);
    
    if (this.events.onConnect) {
      this.events.onConnect(this.sessionId);
    }
  }

  private handleThinkingNodeCreated(payload: ThinkingNodeData): void {
    if (this.events.onThinkingNodeCreated) {
      this.events.onThinkingNodeCreated(payload);
    }
  }

  private handleBlueprintLoaded(payload: { steps: ExecutionStepData[] }): void {
    if (this.events.onBlueprintLoaded) {
      this.events.onBlueprintLoaded(payload.steps);
    }
  }

  private handleStepStarted(payload: { step_id: string; step_name: string; index: number }): void {
    if (this.events.onStepStarted) {
      this.events.onStepStarted(payload.step_id, payload.step_name, payload.index);
    }
  }

  private handleStepCompleted(payload: { step_id: string; result: unknown; duration_ms: number }): void {
    if (this.events.onStepCompleted) {
      this.events.onStepCompleted(payload.step_id, payload.result, payload.duration_ms);
    }
  }

  private handleStepFailed(payload: { step_id: string; error: string }): void {
    if (this.events.onStepFailed) {
      this.events.onStepFailed(payload.step_id, payload.error);
    }
  }

  private handleInterventionNeeded(payload: { step_id: string; step_name: string; reason: string; actions: InterventionActionData[] }): void {
    if (this.events.onInterventionNeeded) {
      this.events.onInterventionNeeded(payload.step_id, payload.reason, payload.actions);
    }
  }

  private handleReplanned(payload: { step_id: string; new_steps: ExecutionStepData[] }): void {
    if (this.events.onReplanned) {
      this.events.onReplanned(payload.step_id, payload.new_steps);
    }
  }

  private handleExecutionCompleted(payload: { success: boolean; summary: string }): void {
    if (this.events.onExecutionCompleted) {
      this.events.onExecutionCompleted(payload.success, payload.summary);
    }
  }

  private handleError(payload: ErrorPayload): void {
    console.error('[Engine] Error:', payload);
    if (this.events.onError) {
      this.events.onError(payload);
    }
  }

  // ============ 公共方法 ============

  send(message: BlueclawMessage): void {
    if (this.connected && this.ws) {
      this.ws.send(JSON.stringify(message));
    } else {
      // 离线时加入队列
      this.messageQueue.push(message);
      console.warn('[Engine] WebSocket not connected, message queued');
    }
  }

  // 清空消息队列（重连后调用）
  flushQueue(): void {
    while (this.messageQueue.length > 0 && this.connected) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  // ============ 便捷方法 ============

  startTask(userInput: string, context?: Record<string, unknown>): void {
    this.send(MessageFactory.createTaskStart(userInput, context));
  }

  selectOption(nodeId: string, optionId: string): void {
    this.send(MessageFactory.createSelectOption(nodeId, optionId));
  }

  provideCustomInput(nodeId: string, customInput: string): void {
    this.send(MessageFactory.createCustomInput(nodeId, customInput));
  }

  confirmExecution(confirmed: boolean): void {
    this.send(MessageFactory.createConfirmExecution(confirmed));
  }

  intervene(stepId: string, actionType: string, customInput?: string): void {
    this.send(MessageFactory.createIntervene(stepId, actionType, customInput));
  }

  pauseExecution(): void {
    this.send(MessageFactory.createPause());
  }

  resumeExecution(): void {
    this.send(MessageFactory.createResume());
  }

  // ============ 状态查询 ============

  isConnected(): boolean {
    return this.connected;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }
}

// ==================== 工厂函数 ====================

export function createEngine(
  wsUrl: string = 'ws://localhost:8765',
  events: PartialEngineEvents = {}
): BlueclawEngine {
  return new BlueclawEngine({ wsUrl }, events);
}
