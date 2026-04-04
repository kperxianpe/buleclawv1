/**
 * ReactFlowAdapter.ts - ReactFlow 渲染适配器
 * 
 * V1 实现：使用 ReactFlow 渲染思考蓝图和执行蓝图
 */

import {
  Node,
  Edge,
  XYPosition,
  NodeProps,
} from 'reactflow';
import {
  ThinkingNodeData,
  ExecutionStepData,
  InterventionActionData,
  NodeStatus,
} from '../../core/protocol/messageTypes';
import {
  BlueprintRenderer,
  RendererConfig,
  Position,
} from '../BlueprintRenderer';

// ==================== 节点类型定义 ====================

export enum ReactFlowNodeType {
  THINKING = 'thinkingNode',
  EXECUTION = 'executionNode',
  INTERVENTION = 'interventionNode',
}

// ==================== 布局计算 ====================

interface LayoutConfig {
  nodeWidth: number;
  nodeHeight: number;
  horizontalSpacing: number;
  verticalSpacing: number;
  startX: number;
  startY: number;
}

const DEFAULT_LAYOUT: LayoutConfig = {
  nodeWidth: 280,
  nodeHeight: 120,
  horizontalSpacing: 100,
  verticalSpacing: 80,
  startX: 50,
  startY: 50,
};

/**
 * 计算节点位置
 * V1: 简单垂直布局，未来可以替换为更复杂的布局算法
 */
function calculateNodePosition(
  index: number,
  layer: number = 0,
  config: LayoutConfig = DEFAULT_LAYOUT
): Position {
  return {
    x: config.startX + layer * (config.nodeWidth + config.horizontalSpacing),
    y: config.startY + index * (config.nodeHeight + config.verticalSpacing),
  };
}

// ==================== 适配器实现 ====================

export interface ReactFlowAdapterCallbacks {
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void;
  fitView: (options?: { padding?: number; duration?: number }) => void;
  setViewport: (viewport: { x: number; y: number; zoom: number }) => void;
}

export class ReactFlowAdapter implements BlueprintRenderer {
  private nodes: Map<string, Node> = new Map();
  private edges: Map<string, Edge> = new Map();
  private container: HTMLElement | null = null;
  private callbacks: ReactFlowAdapterCallbacks | null = null;
  private config: RendererConfig | null = null;
  private layoutConfig: LayoutConfig = DEFAULT_LAYOUT;
  
  // 节点计数器（用于布局）
  private thinkingNodeCount = 0;
  private executionNodeCount = 0;

  constructor(callbacks?: ReactFlowAdapterCallbacks) {
    if (callbacks) {
      this.callbacks = callbacks;
    }
  }

  // ============ 生命周期 ============

  initialize(container: HTMLElement): void {
    this.container = container;
  }

  destroy(): void {
    this.nodes.clear();
    this.edges.clear();
    this.container = null;
    this.callbacks = null;
  }

  setCallbacks(callbacks: ReactFlowAdapterCallbacks): void {
    this.callbacks = callbacks;
  }

  // ============ 思考蓝图操作 ============

  addThinkingNode(node: ThinkingNodeData): void {
    const position = calculateNodePosition(
      this.thinkingNodeCount++,
      0,
      this.layoutConfig
    );

    const reactNode: Node = {
      id: node.id,
      type: ReactFlowNodeType.THINKING,
      position,
      data: {
        ...node,
        onOptionSelect: this.config?.onOptionSelect,
      },
      style: this.getNodeStyle(node.status),
    };

    this.nodes.set(node.id, reactNode);
    this.syncNodes();

    // 如果有前一个思考节点，添加连线
    const prevNodes = Array.from(this.nodes.values()).filter(
      (n) => n.type === ReactFlowNodeType.THINKING && n.id !== node.id
    );
    if (prevNodes.length > 0) {
      const prevNode = prevNodes[prevNodes.length - 1];
      this.addConnection(prevNode.id, node.id);
    }

    this.fitView();
  }

  updateThinkingNode(nodeId: string, updates: Partial<ThinkingNodeData>): void {
    const node = this.nodes.get(nodeId);
    if (!node) return;

    const updatedNode: Node = {
      ...node,
      data: { ...node.data, ...updates },
      style: updates.status ? this.getNodeStyle(updates.status) : node.style,
    };

    this.nodes.set(nodeId, updatedNode);
    this.syncNodes();
  }

  selectThinkingOption(nodeId: string, optionId: string): void {
    this.updateThinkingNode(nodeId, {
      selected_option: optionId,
      status: NodeStatus.SELECTED,
    });
  }

  // ============ 执行蓝图操作 ============

  addExecutionStep(step: ExecutionStepData): void {
    const position = calculateNodePosition(
      this.executionNodeCount++,
      1, // 执行步骤放在第二列
      this.layoutConfig
    );

    const reactNode: Node = {
      id: step.id,
      type: ReactFlowNodeType.EXECUTION,
      position,
      data: {
        ...step,
        onNodeClick: this.config?.onNodeClick,
      },
      style: this.getNodeStyle(step.status),
    };

    this.nodes.set(step.id, reactNode);
    this.syncNodes();

    // 添加依赖连线
    if (step.dependencies && step.dependencies.length > 0) {
      step.dependencies.forEach((depId) => {
        this.addConnection(depId, step.id);
      });
    } else if (this.executionNodeCount > 1) {
      // 没有依赖时，连接到前一个步骤
      const prevNodes = Array.from(this.nodes.values()).filter(
        (n) => n.type === ReactFlowNodeType.EXECUTION && n.id !== step.id
      );
      if (prevNodes.length > 0) {
        const prevNode = prevNodes[prevNodes.length - 1];
        this.addConnection(prevNode.id, step.id);
      }
    }
  }

  addExecutionSteps(steps: ExecutionStepData[]): void {
    steps.forEach((step) => this.addExecutionStep(step));
    this.fitView();
  }

  updateExecutionStep(stepId: string, updates: Partial<ExecutionStepData>): void {
    const node = this.nodes.get(stepId);
    if (!node) return;

    const updatedNode: Node = {
      ...node,
      data: { ...node.data, ...updates },
      style: updates.status ? this.getNodeStyle(updates.status) : node.style,
    };

    this.nodes.set(stepId, updatedNode);
    this.syncNodes();
  }

  setStepStatus(stepId: string, status: NodeStatus): void {
    this.updateExecutionStep(stepId, { status });

    // 更新连线动画状态
    if (status === NodeStatus.RUNNING) {
      this.animateConnectionsTo(stepId);
    }
  }

  // ============ 连线操作 ============

  addConnection(from: string, to: string, animated = false): void {
    const edgeId = `${from}->${to}`;
    
    const edge: Edge = {
      id: edgeId,
      source: from,
      target: to,
      animated,
      style: { stroke: this.getEdgeColor(animated) },
    };

    this.edges.set(edgeId, edge);
    this.syncEdges();
  }

  removeConnection(from: string, to: string): void {
    const edgeId = `${from}->${to}`;
    this.edges.delete(edgeId);
    this.syncEdges();
  }

  // ============ 干预面板 ============

  showInterventionPanel(stepId: string, actions: InterventionActionData[]): void {
    const node = this.nodes.get(stepId);
    if (!node) return;

    // 添加干预节点
    const interventionId = `${stepId}_intervention`;
    const position = {
      x: node.position.x + this.layoutConfig.nodeWidth + 50,
      y: node.position.y,
    };

    const interventionNode: Node = {
      id: interventionId,
      type: ReactFlowNodeType.INTERVENTION,
      position,
      data: {
        stepId,
        actions,
        onAction: this.config?.onInterventionAction,
      },
    };

    this.nodes.set(interventionId, interventionNode);
    this.addConnection(stepId, interventionId, true);
    this.syncNodes();
    this.syncEdges();
    this.focusOnNode(interventionId);
  }

  hideInterventionPanel(): void {
    // 移除所有干预节点
    const interventionNodes = Array.from(this.nodes.values()).filter(
      (n) => n.type === ReactFlowNodeType.INTERVENTION
    );

    interventionNodes.forEach((node) => {
      this.nodes.delete(node.id);
      // 移除相关连线
      Array.from(this.edges.keys()).forEach((edgeId) => {
        if (edgeId.includes(node.id)) {
          this.edges.delete(edgeId);
        }
      });
    });

    this.syncNodes();
    this.syncEdges();
  }

  // ============ 视图操作 ============

  focusOnNode(nodeId: string): void {
    const node = this.nodes.get(nodeId);
    if (!node || !this.callbacks) return;

    // ReactFlow 的 setCenter 需要具体的 center 方法
    // 这里我们通过设置 viewport 来实现
    const { x, y } = node.position;
    this.callbacks.setViewport({
      x: -x + 100,
      y: -y + 100,
      zoom: 1.2,
    });
  }

  setViewport(x: number, y: number, zoom: number): void {
    this.callbacks?.setViewport({ x, y, zoom });
  }

  fitView(): void {
    this.callbacks?.fitView({ padding: 0.2, duration: 500 });
  }

  // ============ 动画 ============

  setNodeAnimation(nodeId: string, animation: 'pulse' | 'glow' | 'none'): void {
    const node = this.nodes.get(nodeId);
    if (!node) return;

    const updatedNode: Node = {
      ...node,
      data: { ...node.data, animation },
    };

    this.nodes.set(nodeId, updatedNode);
    this.syncNodes();
  }

  highlightPath(nodeIds: string[]): void {
    // 重置所有连线
    this.edges.forEach((edge) => {
      edge.animated = false;
      edge.style = { stroke: this.getEdgeColor(false) };
    });

    // 高亮路径上的连线
    for (let i = 0; i < nodeIds.length - 1; i++) {
      const from = nodeIds[i];
      const to = nodeIds[i + 1];
      const edgeId = `${from}->${to}`;
      const edge = this.edges.get(edgeId);
      
      if (edge) {
        edge.animated = true;
        edge.style = { stroke: this.getEdgeColor(true) };
      }
    }

    this.syncEdges();
  }

  // ============ 导出 ============

  async exportImage(format: 'png' | 'svg' = 'png'): Promise<string> {
    // ReactFlow 的导出功能需要在组件层实现
    // 这里返回空字符串，实际导出由组件处理
    console.warn('Export image should be implemented in ReactFlow component');
    return '';
  }

  // ============ 内部方法 ============

  private syncNodes(): void {
    if (this.callbacks) {
      this.callbacks.setNodes(Array.from(this.nodes.values()));
    }
  }

  private syncEdges(): void {
    if (this.callbacks) {
      this.callbacks.setEdges(Array.from(this.edges.values()));
    }
  }

  private getNodeStyle(status: NodeStatus | string): React.CSSProperties {
    const baseStyle: React.CSSProperties = {
      borderRadius: '8px',
      border: '2px solid',
    };

    switch (status) {
      case NodeStatus.PENDING:
        return { ...baseStyle, borderColor: '#e0e0e0', background: '#ffffff' };
      case NodeStatus.RUNNING:
        return { ...baseStyle, borderColor: '#2196f3', background: '#e3f2fd' };
      case NodeStatus.COMPLETED:
        return { ...baseStyle, borderColor: '#4caf50', background: '#e8f5e9' };
      case NodeStatus.FAILED:
        return { ...baseStyle, borderColor: '#f44336', background: '#ffebee' };
      case NodeStatus.SELECTED:
        return { ...baseStyle, borderColor: '#9c27b0', background: '#f3e5f5' };
      default:
        return { ...baseStyle, borderColor: '#e0e0e0', background: '#ffffff' };
    }
  }

  private getEdgeColor(animated: boolean): string {
    return animated ? '#2196f3' : '#b0b0b0';
  }

  private animateConnectionsTo(nodeId: string): void {
    this.edges.forEach((edge) => {
      if (edge.target === nodeId) {
        edge.animated = true;
        edge.style = { stroke: this.getEdgeColor(true) };
      }
    });
    this.syncEdges();
  }

  // ============ 获取状态 ============

  getNodes(): Node[] {
    return Array.from(this.nodes.values());
  }

  getEdges(): Edge[] {
    return Array.from(this.edges.values());
  }
}

// ==================== 工厂注册 ====================

import { registerRenderer } from '../BlueprintRenderer';

registerRenderer('reactflow', {
  create: (config: RendererConfig) => {
    const adapter = new ReactFlowAdapter();
    // 需要在 ReactFlow 组件初始化后设置 callbacks
    return adapter;
  },
});
