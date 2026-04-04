/**
 * BlueprintRenderer.ts - 渲染适配器接口
 * 
 * 定义渲染层必须实现的接口
 * V1: ReactFlowAdapter
 * V2: CanvasMindAdapter (未来)
 */

import { CSSProperties } from 'react';
import {
  ThinkingNodeData,
  ExecutionStepData,
  InterventionActionData,
  NodeStatus,
} from '../core/protocol/messageTypes';

// ==================== 渲染节点数据 ====================

export interface Position {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface RenderedNode extends ThinkingNodeData {
  position: Position;
  size?: Size;
  style?: CSSProperties;
}

export interface RenderedStep extends ExecutionStepData {
  position: Position;
  size?: Size;
  style?: CSSProperties;
}

export interface Connection {
  id: string;
  from: string;
  to: string;
  animated?: boolean;
  style?: CSSProperties;
}

// ==================== 渲染器接口 ====================

export interface BlueprintRenderer {
  // ============ 生命周期 ============
  
  /**
   * 初始化画布
   * @param container 容器元素
   */
  initialize(container: HTMLElement): void;
  
  /**
   * 清理资源
   */
  destroy(): void;
  
  // ============ 思考蓝图操作 ============
  
  /**
   * 添加思考节点
   * @param node 节点数据
   * @param options 选项数据（如果是选项节点）
   */
  addThinkingNode(node: ThinkingNodeData): void;
  
  /**
   * 更新思考节点
   * @param nodeId 节点ID
   * @param updates 更新数据
   */
  updateThinkingNode(nodeId: string, updates: Partial<ThinkingNodeData>): void;
  
  /**
   * 标记选项已选择
   * @param nodeId 节点ID
   * @param optionId 选项ID
   */
  selectThinkingOption(nodeId: string, optionId: string): void;
  
  // ============ 执行蓝图操作 ============
  
  /**
   * 添加执行步骤
   * @param step 步骤数据
   */
  addExecutionStep(step: ExecutionStepData): void;
  
  /**
   * 批量添加执行步骤
   * @param steps 步骤数据数组
   */
  addExecutionSteps(steps: ExecutionStepData[]): void;
  
  /**
   * 更新执行步骤
   * @param stepId 步骤ID
   * @param updates 更新数据
   */
  updateExecutionStep(stepId: string, updates: Partial<ExecutionStepData>): void;
  
  /**
   * 设置步骤状态
   * @param stepId 步骤ID
   * @param status 状态
   */
  setStepStatus(stepId: string, status: NodeStatus): void;
  
  // ============ 连线操作 ============
  
  /**
   * 添加连线
   * @param from 起始节点ID
   * @param to 目标节点ID
   * @param animated 是否动画
   */
  addConnection(from: string, to: string, animated?: boolean): void;
  
  /**
   * 移除连线
   * @param from 起始节点ID
   * @param to 目标节点ID
   */
  removeConnection(from: string, to: string): void;
  
  // ============ 干预面板 ============
  
  /**
   * 显示干预面板
   * @param stepId 步骤ID
   * @param actions 可用操作
   */
  showInterventionPanel(stepId: string, actions: InterventionActionData[]): void;
  
  /**
   * 隐藏干预面板
   */
  hideInterventionPanel(): void;
  
  // ============ 视图操作 ============
  
  /**
   * 聚焦到指定节点
   * @param nodeId 节点ID
   */
  focusOnNode(nodeId: string): void;
  
  /**
   * 设置视口
   * @param x X坐标
   * @param y Y坐标
   * @param zoom 缩放级别
   */
  setViewport(x: number, y: number, zoom: number): void;
  
  /**
   * 适应视图到所有节点
   */
  fitView(): void;
  
  // ============ 动画 ============
  
  /**
   * 设置节点动画
   * @param nodeId 节点ID
   * @param animation 动画类型
   */
  setNodeAnimation(nodeId: string, animation: 'pulse' | 'glow' | 'none'): void;
  
  /**
   * 高亮路径
   * @param nodeIds 节点ID数组（从起点到终点）
   */
  highlightPath(nodeIds: string[]): void;
  
  // ============ 导出 ============
  
  /**
   * 导出当前视图为图片
   * @param format 图片格式
   */
  exportImage(format?: 'png' | 'svg'): Promise<string>;
}

// ==================== 渲染器类型 ====================

export type RendererType = 'reactflow' | 'canvasmind';

// ==================== 渲染器配置 ====================

export interface RendererConfig {
  type: RendererType;
  container: HTMLElement;
  
  // 回调函数
  onNodeClick?: (nodeId: string, nodeType: 'thinking' | 'execution') => void;
  onOptionSelect?: (nodeId: string, optionId: string) => void;
  onInterventionAction?: (stepId: string, actionType: string) => void;
  onViewportChange?: (x: number, y: number, zoom: number) => void;
  
  // 样式配置
  theme?: 'light' | 'dark';
  nodeSpacing?: number;
  layerSpacing?: number;
}

// ==================== 渲染器工厂 ====================

export interface RendererFactory {
  create(config: RendererConfig): BlueprintRenderer;
}

// 渲染器注册表
const rendererRegistry: Map<RendererType, RendererFactory> = new Map();

export function registerRenderer(type: RendererType, factory: RendererFactory): void {
  rendererRegistry.set(type, factory);
}

export function createRenderer(config: RendererConfig): BlueprintRenderer {
  const factory = rendererRegistry.get(config.type);
  if (!factory) {
    throw new Error(`Unknown renderer type: ${config.type}`);
  }
  return factory.create(config);
}

// ==================== 便捷类型 ====================

export type NodeUpdateCallback = (nodeId: string, updates: Partial<ThinkingNodeData>) => void;
export type StepUpdateCallback = (stepId: string, updates: Partial<ExecutionStepData>) => void;
export type NodeClickCallback = (nodeId: string, nodeType: 'thinking' | 'execution') => void;
export type OptionSelectCallback = (nodeId: string, optionId: string) => void;
export type InterventionActionCallback = (stepId: string, actionType: string) => void;
