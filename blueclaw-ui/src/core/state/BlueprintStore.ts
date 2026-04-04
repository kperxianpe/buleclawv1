/**
 * BlueprintStore.ts - 状态管理
 * 
 * 使用 Zustand 管理应用状态
 * 纯数据层，不依赖具体渲染实现
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import {
  ThinkingNodeData,
  ExecutionStepData,
  InterventionActionData,
  NodeStatus,
  Phase,
} from '../protocol/messageTypes';

// ==================== 状态接口 ====================

export interface BlueprintState {
  // 连接状态
  isConnected: boolean;
  sessionId: string | null;
  connectionError: string | null;

  // 应用阶段
  currentPhase: Phase;
  progress: number;
  statusMessage: string;

  // 思考阶段数据
  thinkingNodes: Map<string, ThinkingNodeData>;
  activeNodeId: string | null;

  // 执行阶段数据
  executionSteps: Map<string, ExecutionStepData>;
  currentStepId: string | null;

  // 干预状态
  isIntervening: boolean;
  interventionStepId: string | null;
  interventionActions: InterventionActionData[];
  interventionReason: string;

  // 历史（用于回溯）
  history: HistoryEntry[];
}

export interface HistoryEntry {
  timestamp: number;
  type: 'node_added' | 'node_selected' | 'step_started' | 'step_completed' | 'step_failed' | 'intervention';
  data: unknown;
}

// ==================== Actions 接口 ====================

export interface BlueprintActions {
  // 连接操作
  setConnected: (connected: boolean, sessionId?: string) => void;
  setConnectionError: (error: string | null) => void;

  // 阶段操作
  setPhase: (phase: Phase) => void;
  setProgress: (progress: number) => void;
  setStatusMessage: (message: string) => void;

  // 思考节点操作
  addThinkingNode: (node: ThinkingNodeData) => void;
  updateThinkingNode: (nodeId: string, updates: Partial<ThinkingNodeData>) => void;
  selectThinkingOption: (nodeId: string, optionId: string) => void;
  setActiveNode: (nodeId: string | null) => void;

  // 执行步骤操作
  addExecutionSteps: (steps: ExecutionStepData[]) => void;
  updateExecutionStep: (stepId: string, updates: Partial<ExecutionStepData>) => void;
  setStepStatus: (stepId: string, status: NodeStatus) => void;
  setCurrentStep: (stepId: string | null) => void;

  // 干预操作
  showIntervention: (stepId: string, reason: string, actions: InterventionActionData[]) => void;
  hideIntervention: () => void;

  // 历史操作
  addHistoryEntry: (type: HistoryEntry['type'], data: unknown) => void;

  // 重置
  reset: () => void;
}

// ==================== 初始状态 ====================

const initialState: BlueprintState = {
  isConnected: false,
  sessionId: null,
  connectionError: null,

  currentPhase: Phase.IDLE,
  progress: 0,
  statusMessage: '准备就绪',

  thinkingNodes: new Map(),
  activeNodeId: null,

  executionSteps: new Map(),
  currentStepId: null,

  isIntervening: false,
  interventionStepId: null,
  interventionActions: [],
  interventionReason: '',

  history: [],
};

// ==================== Store 创建 ====================

export const useBlueprintStore = create<BlueprintState & BlueprintActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // 连接操作
      setConnected: (connected, sessionId) =>
        set({
          isConnected: connected,
          sessionId: sessionId || null,
          connectionError: connected ? null : get().connectionError,
        }),

      setConnectionError: (error) =>
        set({
          connectionError: error,
          isConnected: false,
        }),

      // 阶段操作
      setPhase: (phase) =>
        set({
          currentPhase: phase,
        }),

      setProgress: (progress) =>
        set({
          progress: Math.min(100, Math.max(0, progress)),
        }),

      setStatusMessage: (message) =>
        set({
          statusMessage: message,
        }),

      // 思考节点操作
      addThinkingNode: (node) =>
        set((state) => {
          const newNodes = new Map(state.thinkingNodes);
          newNodes.set(node.id, node);
          return {
            thinkingNodes: newNodes,
            activeNodeId: node.id,
          };
        }),

      updateThinkingNode: (nodeId, updates) =>
        set((state) => {
          const node = state.thinkingNodes.get(nodeId);
          if (!node) return {};

          const newNodes = new Map(state.thinkingNodes);
          newNodes.set(nodeId, { ...node, ...updates });
          return { thinkingNodes: newNodes };
        }),

      selectThinkingOption: (nodeId, optionId) =>
        set((state) => {
          const node = state.thinkingNodes.get(nodeId);
          if (!node) return {};

          const newNodes = new Map(state.thinkingNodes);
          newNodes.set(nodeId, {
            ...node,
            selected_option: optionId,
            status: NodeStatus.SELECTED,
          });
          return { thinkingNodes: newNodes };
        }),

      setActiveNode: (nodeId) =>
        set({
          activeNodeId: nodeId,
        }),

      // 执行步骤操作
      addExecutionSteps: (steps) =>
        set((state) => {
          const newSteps = new Map(state.executionSteps);
          steps.forEach((step) => {
            newSteps.set(step.id, step);
          });
          return {
            executionSteps: newSteps,
            currentPhase: Phase.EXECUTING,
          };
        }),

      updateExecutionStep: (stepId, updates) =>
        set((state) => {
          const step = state.executionSteps.get(stepId);
          if (!step) return {};

          const newSteps = new Map(state.executionSteps);
          newSteps.set(stepId, { ...step, ...updates });
          return { executionSteps: newSteps };
        }),

      setStepStatus: (stepId, status) =>
        set((state) => {
          const step = state.executionSteps.get(stepId);
          if (!step) return {};

          const newSteps = new Map(state.executionSteps);
          newSteps.set(stepId, { ...step, status });

          // 更新当前步骤
          const currentStepId = status === NodeStatus.RUNNING ? stepId : state.currentStepId;

          // 计算进度
          const steps = Array.from(newSteps.values());
          const completed = steps.filter((s) => s.status === NodeStatus.COMPLETED).length;
          const progress = steps.length > 0 ? Math.round((completed / steps.length) * 100) : 0;

          return {
            executionSteps: newSteps,
            currentStepId,
            progress,
          };
        }),

      setCurrentStep: (stepId) =>
        set({
          currentStepId: stepId,
        }),

      // 干预操作
      showIntervention: (stepId, reason, actions) =>
        set({
          isIntervening: true,
          interventionStepId: stepId,
          interventionReason: reason,
          interventionActions: actions,
          currentPhase: Phase.INTERVENING,
        }),

      hideIntervention: () =>
        set({
          isIntervening: false,
          interventionStepId: null,
          interventionReason: '',
          interventionActions: [],
        }),

      // 历史操作
      addHistoryEntry: (type, data) =>
        set((state) => ({
          history: [
            ...state.history,
            {
              timestamp: Date.now(),
              type,
              data,
            },
          ],
        })),

      // 重置
      reset: () =>
        set({
          ...initialState,
          isConnected: get().isConnected,
          sessionId: get().sessionId,
        }),
    }),
    {
      name: 'blueclaw-store',
    }
  )
);

// ==================== 选择器 ====================

export const selectThinkingNodes = (state: BlueprintState): ThinkingNodeData[] =>
  Array.from(state.thinkingNodes.values());

export const selectExecutionSteps = (state: BlueprintState): ExecutionStepData[] =>
  Array.from(state.executionSteps.values());

export const selectActiveNode = (state: BlueprintState): ThinkingNodeData | null =>
  state.activeNodeId ? state.thinkingNodes.get(state.activeNodeId) || null : null;

export const selectCurrentStep = (state: BlueprintState): ExecutionStepData | null =>
  state.currentStepId ? state.executionSteps.get(state.currentStepId) || null : null;

export const selectCompletedSteps = (state: BlueprintState): ExecutionStepData[] =>
  Array.from(state.executionSteps.values()).filter(
    (step) => step.status === NodeStatus.COMPLETED
  );

export const selectFailedSteps = (state: BlueprintState): ExecutionStepData[] =>
  Array.from(state.executionSteps.values()).filter(
    (step) => step.status === NodeStatus.FAILED
  );

// ==================== 导出便捷 hooks ====================

export function useConnectionState() {
  return useBlueprintStore((state) => ({
    isConnected: state.isConnected,
    sessionId: state.sessionId,
    error: state.connectionError,
  }));
}

export function usePhaseState() {
  return useBlueprintStore((state) => ({
    phase: state.currentPhase,
    progress: state.progress,
    statusMessage: state.statusMessage,
  }));
}

export function useThinkingNodes() {
  return useBlueprintStore((state) => ({
    nodes: Array.from(state.thinkingNodes.values()),
    activeNodeId: state.activeNodeId,
  }));
}

export function useExecutionSteps() {
  return useBlueprintStore((state) => ({
    steps: Array.from(state.executionSteps.values()),
    currentStepId: state.currentStepId,
  }));
}

export function useInterventionState() {
  return useBlueprintStore((state) => ({
    isIntervening: state.isIntervening,
    stepId: state.interventionStepId,
    reason: state.interventionReason,
    actions: state.interventionActions,
  }));
}
