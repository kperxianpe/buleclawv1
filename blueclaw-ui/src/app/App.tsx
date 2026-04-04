/**
 * App.tsx - Blueclaw 主应用组件
 * 
 * 整合引擎客户端、状态管理和渲染适配器
 * 支持切换不同的渲染引擎（ReactFlow / CanvasMind）
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  Panel,
} from 'reactflow';

// Core imports
import { BlueclawEngine, createEngine } from '../core/engine/BlueclawEngine';
import { useBlueprintStore, useConnectionState, usePhaseState, useInterventionState } from '../core/state/BlueprintStore';
import { MessageType, Phase, NodeStatus, ExecutionStepData, InterventionActionData } from '../core/protocol/messageTypes';

// Adapter imports
import { BlueprintRenderer, RendererType } from '../adapters/BlueprintRenderer';
import { ReactFlowAdapter, ReactFlowAdapterCallbacks } from '../adapters/reactflow/ReactFlowAdapter';

// Node components
import { ThinkingNode } from '../adapters/reactflow/components/ThinkingNode';
import { ExecutionNode } from '../adapters/reactflow/components/ExecutionNode';
import { InterventionNode } from '../adapters/reactflow/components/InterventionNode';

// Node type definitions
const nodeTypes = {
  thinkingNode: ThinkingNode,
  executionNode: ExecutionNode,
  interventionNode: InterventionNode,
};

// ==================== 主应用组件 ====================

const AppContent: React.FC = () => {
  // Refs
  const engineRef = useRef<BlueclawEngine | null>(null);
  const adapterRef = useRef<ReactFlowAdapter | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // ReactFlow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Local state
  const [inputValue, setInputValue] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [rendererType, setRendererType] = useState<RendererType>('reactflow');

  // Store state
  const { isConnected, sessionId, error: connectionError } = useConnectionState();
  const { phase, progress, statusMessage } = usePhaseState();
  const { isIntervening, stepId: interventionStepId, actions: interventionActions, reason: interventionReason } = useInterventionState();

  // Store actions
  const storeActions = useBlueprintStore((state) => ({
    setConnected: state.setConnected,
    setConnectionError: state.setConnectionError,
    setPhase: state.setPhase,
    setProgress: state.setProgress,
    setStatusMessage: state.setStatusMessage,
    addThinkingNode: state.addThinkingNode,
    addExecutionSteps: state.addExecutionSteps,
    setStepStatus: state.setStepStatus,
    showIntervention: state.showIntervention,
    hideIntervention: state.hideIntervention,
    reset: state.reset,
  }));

  // ==================== 初始化 ====================

  useEffect(() => {
    // Create adapter callbacks
    const callbacks: ReactFlowAdapterCallbacks = {
      setNodes,
      setEdges,
      fitView: (options) => {
        // ReactFlow's fitView is available via ref in a real implementation
        console.log('fitView called', options);
      },
      setViewport: (viewport) => {
        console.log('setViewport called', viewport);
      },
    };

    // Create adapter
    adapterRef.current = new ReactFlowAdapter(callbacks);

    // Create engine with event handlers
    const engine = createEngine('ws://localhost:8765', {
      onConnect: (sessionId) => {
        storeActions.setConnected(true, sessionId);
        addLog(`已连接到服务器 (会话: ${sessionId})`);
      },
      onDisconnect: (reason) => {
        storeActions.setConnected(false);
        addLog(`连接断开: ${reason}`);
      },
      onError: (error) => {
        storeActions.setConnectionError(error.error_message);
        addLog(`错误: ${error.error_message}`);
      },
      onThinkingNodeCreated: (node) => {
        storeActions.addThinkingNode(node);
        adapterRef.current?.addThinkingNode(node);
        addLog(`创建思考节点: ${node.question.slice(0, 30)}...`);
      },
      onBlueprintLoaded: (steps) => {
        storeActions.addExecutionSteps(steps);
        adapterRef.current?.addExecutionSteps(steps);
        addLog(`加载执行蓝图: ${steps.length} 个步骤`);
      },
      onStepStarted: (stepId, stepName, index) => {
        storeActions.setStepStatus(stepId, NodeStatus.RUNNING);
        adapterRef.current?.setStepStatus(stepId, NodeStatus.RUNNING);
        storeActions.setStatusMessage(`执行: ${stepName}`);
        addLog(`开始步骤 ${index + 1}: ${stepName}`);
      },
      onStepCompleted: (stepId, result, durationMs) => {
        storeActions.setStepStatus(stepId, NodeStatus.COMPLETED);
        adapterRef.current?.setStepStatus(stepId, NodeStatus.COMPLETED);
        addLog(`步骤完成: ${stepId} (${Math.round(durationMs)}ms)`);
      },
      onStepFailed: (stepId, error) => {
        storeActions.setStepStatus(stepId, NodeStatus.FAILED);
        adapterRef.current?.setStepStatus(stepId, NodeStatus.FAILED);
        addLog(`步骤失败: ${stepId} - ${error}`);
      },
      onInterventionNeeded: (stepId, reason, actions) => {
        storeActions.showIntervention(stepId, reason, actions);
        adapterRef.current?.showInterventionPanel(stepId, actions);
        addLog(`需要干预: ${reason}`);
      },
      onExecutionCompleted: (success, summary) => {
        storeActions.setPhase(Phase.COMPLETED);
        storeActions.setStatusMessage(summary);
        addLog(`执行完成: ${summary}`);
      },
      onMessage: (message) => {
        addLog(message);
      },
    });

    engineRef.current = engine;

    // Connect to server
    engine.connect().catch((err) => {
      storeActions.setConnectionError(err.message);
      addLog(`连接失败: ${err.message}`);
    });

    return () => {
      engine.disconnect();
    };
  }, []);

  // ==================== 工具函数 ====================

  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev.slice(-99), `[${timestamp}] ${message}`]);
  }, []);

  // ==================== 事件处理器 ====================

  const handleSendMessage = useCallback(() => {
    if (!inputValue.trim() || !engineRef.current) return;

    engineRef.current.startTask(inputValue);
    setInputValue('');
    addLog(`发送任务: ${inputValue}`);
  }, [inputValue, addLog]);

  const handleOptionSelect = useCallback((nodeId: string, optionId: string) => {
    if (!engineRef.current) return;

    engineRef.current.selectOption(nodeId, optionId);
    addLog(`选择选项: ${optionId}`);
  }, [addLog]);

  const handleInterventionAction = useCallback((stepId: string, actionType: string) => {
    if (!engineRef.current) return;

    engineRef.current.intervene(stepId, actionType);
    storeActions.hideIntervention();
    adapterRef.current?.hideInterventionPanel();
    addLog(`干预操作: ${actionType}`);
  }, [addLog, storeActions]);

  const handlePause = useCallback(() => {
    if (!engineRef.current) return;

    if (phase === Phase.EXECUTING) {
      engineRef.current.pauseExecution();
      addLog('暂停执行');
    }
  }, [phase, addLog]);

  const handleResume = useCallback(() => {
    if (!engineRef.current) return;

    engineRef.current.resumeExecution();
    addLog('恢复执行');
  }, [addLog]);

  const handleReset = useCallback(() => {
    storeActions.reset();
    setNodes([]);
    setEdges([]);
    addLog('重置状态');
  }, [storeActions, setNodes, setEdges, addLog]);

  // ==================== 渲染 ====================

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>🦀 Blueclaw v1.0</h1>
          <span style={styles.subtitle}>AI Self-Operating Canvas</span>
        </div>
        <div style={styles.headerRight}>
          <ConnectionStatus isConnected={isConnected} sessionId={sessionId} />
          <select
            value={rendererType}
            onChange={(e) => setRendererType(e.target.value as RendererType)}
            style={styles.select}
          >
            <option value="reactflow">ReactFlow (V1)</option>
            <option value="canvasmind">CanvasMind (V2)</option>
          </select>
        </div>
      </header>

      {/* Main content */}
      <div style={styles.main}>
        {/* Left panel - Chat & Input */}
        <div style={styles.leftPanel}>
          {/* Status */}
          <div style={styles.statusBar}>
            <StatusBadge phase={phase} />
            <ProgressBar progress={progress} />
            <span style={styles.statusText}>{statusMessage}</span>
          </div>

          {/* Input area */}
          <div style={styles.inputArea}>
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.metaKey) {
                  handleSendMessage();
                }
              }}
              placeholder="输入你的任务... (Cmd+Enter 发送)"
              style={styles.textarea}
              rows={3}
            />
            <button
              onClick={handleSendMessage}
              disabled={!isConnected || !inputValue.trim()}
              style={{
                ...styles.sendButton,
                opacity: !isConnected || !inputValue.trim() ? 0.5 : 1,
              }}
            >
              发送
            </button>
          </div>

          {/* Quick actions */}
          <div style={styles.quickActions}>
            <QuickActionButton
              label="✈️ 规划旅行"
              onClick={() => setInputValue('我想规划一个周末短途旅行')}
            />
            <QuickActionButton
              label="📁 列出文件"
              onClick={() => setInputValue('列出当前目录的文件')}
            />
            <QuickActionButton
              label="🐍 写代码"
              onClick={() => setInputValue('写一个Python脚本批量重命名文件')}
            />
          </div>

          {/* Control buttons */}
          <div style={styles.controls}>
            <ControlButton onClick={handlePause} disabled={phase !== Phase.EXECUTING}>
              ⏸️ 暂停
            </ControlButton>
            <ControlButton onClick={handleResume} disabled={phase !== Phase.EXECUTING}>
              ▶️ 继续
            </ControlButton>
            <ControlButton onClick={handleReset}>🔄 重置</ControlButton>
          </div>

          {/* Logs */}
          <div style={styles.logsContainer}>
            <div style={styles.logsHeader}>📜 日志</div>
            <div style={styles.logs}>
              {logs.map((log, i) => (
                <div key={i} style={styles.logLine}>{log}</div>
              ))}
            </div>
          </div>
        </div>

        {/* Right panel - Canvas */}
        <div style={styles.rightPanel} ref={containerRef}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            style={{ background: '#fafafa' }}
          >
            <Background />
            <Controls />
            <MiniMap />
            <Panel position="top-right">
              <div style={styles.panel}>
                <div>协议版本: 1.0.0</div>
                <div>渲染器: {rendererType}</div>
                <div>节点数: {nodes.length}</div>
                <div>连线数: {edges.length}</div>
              </div>
            </Panel>
          </ReactFlow>
        </div>
      </div>

      {/* Intervention Modal */}
      {isIntervening && (
        <InterventionModal
          stepId={interventionStepId!}
          reason={interventionReason}
          actions={interventionActions}
          onAction={handleInterventionAction}
          onClose={() => {
            storeActions.hideIntervention();
            adapterRef.current?.hideInterventionPanel();
          }}
        />
      )}

      {/* Connection Error */}
      {connectionError && (
        <ErrorToast message={connectionError} onClose={() => storeActions.setConnectionError(null)} />
      )}
    </div>
  );
};

// ==================== 子组件 ====================

const ConnectionStatus: React.FC<{ isConnected: boolean; sessionId: string | null }> = ({
  isConnected,
  sessionId,
}) => (
  <div style={styles.connectionStatus}>
    <span style={{ ...styles.dot, background: isConnected ? '#4caf50' : '#f44336' }} />
    <span style={styles.connectionText}>
      {isConnected ? `已连接 (${sessionId?.slice(0, 6)})` : '未连接'}
    </span>
  </div>
);

const StatusBadge: React.FC<{ phase: Phase }> = ({ phase }) => {
  const colors: Record<Phase, string> = {
    [Phase.IDLE]: '#9e9e9e',
    [Phase.THINKING]: '#2196f3',
    [Phase.EXECUTING]: '#ff9800',
    [Phase.INTERVENING]: '#f44336',
    [Phase.COMPLETED]: '#4caf50',
  };

  const labels: Record<Phase, string> = {
    [Phase.IDLE]: '空闲',
    [Phase.THINKING]: '思考中',
    [Phase.EXECUTING]: '执行中',
    [Phase.INTERVENING]: '干预中',
    [Phase.COMPLETED]: '已完成',
  };

  return (
    <span style={{ ...styles.badge, background: colors[phase] }}>
      {labels[phase]}
    </span>
  );
};

const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
  <div style={styles.progressContainer}>
    <div style={{ ...styles.progressBar, width: `${progress}%` }} />
    <span style={styles.progressText}>{progress}%</span>
  </div>
);

const QuickActionButton: React.FC<{ label: string; onClick: () => void }> = ({ label, onClick }) => (
  <button onClick={onClick} style={styles.quickActionButton}>
    {label}
  </button>
);

const ControlButton: React.FC<{ onClick: () => void; disabled?: boolean; children: React.ReactNode }> = ({
  onClick,
  disabled,
  children,
}) => (
  <button onClick={onClick} disabled={disabled} style={{ ...styles.controlButton, opacity: disabled ? 0.5 : 1 }}>
    {children}
  </button>
);

const InterventionModal: React.FC<{
  stepId: string;
  reason: string;
  actions: InterventionActionData[];
  onAction: (stepId: string, actionType: string) => void;
  onClose: () => void;
}> = ({ stepId, reason, actions, onAction, onClose }) => (
  <div style={styles.modalOverlay}>
    <div style={styles.modal}>
      <h3 style={styles.modalTitle}>⚠️ 需要干预</h3>
      <p style={styles.modalReason}>{reason}</p>
      <div style={styles.modalActions}>
        {actions.map((action) => (
          <button
            key={action.type}
            onClick={() => onAction(stepId, action.type)}
            style={styles.modalActionButton}
          >
            <div style={styles.modalActionLabel}>{action.label}</div>
            <div style={styles.modalActionDesc}>{action.description}</div>
          </button>
        ))}
      </div>
      <button onClick={onClose} style={styles.modalClose}>关闭</button>
    </div>
  </div>
);

const ErrorToast: React.FC<{ message: string; onClose: () => void }> = ({ message, onClose }) => (
  <div style={styles.errorToast}>
    <span>❌ {message}</span>
    <button onClick={onClose} style={styles.errorClose}>×</button>
  </div>
);

// ==================== Styles ====================

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#f5f5f5',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 20px',
    background: '#fff',
    borderBottom: '1px solid #e0e0e0',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#333',
    margin: 0,
  },
  subtitle: {
    fontSize: '13px',
    color: '#666',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  connectionStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  dot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  connectionText: {
    fontSize: '13px',
    color: '#666',
  },
  select: {
    padding: '6px 12px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    fontSize: '13px',
  },
  main: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  leftPanel: {
    width: '360px',
    display: 'flex',
    flexDirection: 'column',
    background: '#fff',
    borderRight: '1px solid #e0e0e0',
  },
  rightPanel: {
    flex: 1,
    position: 'relative',
  },
  statusBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    borderBottom: '1px solid #f0f0f0',
  },
  badge: {
    padding: '4px 10px',
    borderRadius: '4px',
    color: '#fff',
    fontSize: '12px',
    fontWeight: 500,
  },
  progressContainer: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  progressBar: {
    flex: 1,
    height: '6px',
    background: '#e0e0e0',
    borderRadius: '3px',
    position: 'relative',
  },
  progressText: {
    fontSize: '12px',
    color: '#666',
    minWidth: '36px',
  },
  statusText: {
    fontSize: '12px',
    color: '#666',
  },
  inputArea: {
    padding: '16px',
    borderBottom: '1px solid #f0f0f0',
  },
  textarea: {
    width: '100%',
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '14px',
    resize: 'none',
    marginBottom: '12px',
  },
  sendButton: {
    width: '100%',
    padding: '10px',
    background: '#2196f3',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
  },
  quickActions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '12px 16px',
    borderBottom: '1px solid #f0f0f0',
  },
  quickActionButton: {
    padding: '8px 12px',
    background: '#f5f5f5',
    border: '1px solid #e0e0e0',
    borderRadius: '6px',
    fontSize: '13px',
    cursor: 'pointer',
    textAlign: 'left',
  },
  controls: {
    display: 'flex',
    gap: '8px',
    padding: '12px 16px',
    borderBottom: '1px solid #f0f0f0',
  },
  controlButton: {
    flex: 1,
    padding: '8px',
    background: '#f5f5f5',
    border: '1px solid #e0e0e0',
    borderRadius: '6px',
    fontSize: '13px',
    cursor: 'pointer',
  },
  logsContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  logsHeader: {
    padding: '12px 16px',
    fontSize: '13px',
    fontWeight: 500,
    color: '#333',
    borderBottom: '1px solid #f0f0f0',
  },
  logs: {
    flex: 1,
    overflow: 'auto',
    padding: '12px 16px',
    fontSize: '12px',
    fontFamily: 'monospace',
    background: '#1e1e1e',
    color: '#d4d4d4',
  },
  logLine: {
    marginBottom: '4px',
    lineHeight: 1.5,
  },
  panel: {
    padding: '12px',
    background: '#fff',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    fontSize: '12px',
    color: '#666',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: '#fff',
    borderRadius: '12px',
    padding: '24px',
    minWidth: '400px',
    maxWidth: '500px',
  },
  modalTitle: {
    margin: '0 0 12px 0',
    fontSize: '18px',
    color: '#e65100',
  },
  modalReason: {
    margin: '0 0 20px 0',
    color: '#666',
    fontSize: '14px',
  },
  modalActions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    marginBottom: '16px',
  },
  modalActionButton: {
    padding: '12px',
    background: '#f5f5f5',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    cursor: 'pointer',
    textAlign: 'left',
  },
  modalActionLabel: {
    fontWeight: 500,
    fontSize: '14px',
    color: '#333',
  },
  modalActionDesc: {
    fontSize: '12px',
    color: '#666',
    marginTop: '4px',
  },
  modalClose: {
    width: '100%',
    padding: '10px',
    background: '#fff',
    border: '1px solid #ddd',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  errorToast: {
    position: 'fixed',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    background: '#f44336',
    color: '#fff',
    padding: '12px 20px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    zIndex: 1000,
  },
  errorClose: {
    background: 'none',
    border: 'none',
    color: '#fff',
    fontSize: '20px',
    cursor: 'pointer',
  },
};

// ==================== 导出 ====================

const App: React.FC = () => (
  <ReactFlowProvider>
    <AppContent />
  </ReactFlowProvider>
);

export default App;
