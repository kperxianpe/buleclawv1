/**
 * ExecutionNode.tsx - 执行步骤节点组件
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { ExecutionStepData, NodeStatus } from '../../../core/protocol/messageTypes';

interface ExecutionNodeComponentData extends ExecutionStepData {
  onNodeClick?: (nodeId: string, nodeType: 'execution') => void;
  animation?: 'pulse' | 'glow' | 'none';
}

export const ExecutionNode: React.FC<NodeProps<ExecutionNodeComponentData>> = ({ 
  id, 
  data,
  selected 
}) => {
  const { name, description, status, result, error, duration_ms, onNodeClick } = data;

  const handleClick = () => {
    onNodeClick?.(id, 'execution');
  };

  const getStatusIcon = () => {
    switch (status) {
      case NodeStatus.PENDING:
        return '⏳';
      case NodeStatus.RUNNING:
        return '🔄';
      case NodeStatus.COMPLETED:
        return '✅';
      case NodeStatus.FAILED:
        return '❌';
      case NodeStatus.SKIPPED:
        return '⏭️';
      default:
        return '⏳';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case NodeStatus.PENDING:
        return { border: '#e0e0e0', bg: '#ffffff', text: '#666' };
      case NodeStatus.RUNNING:
        return { border: '#2196f3', bg: '#e3f2fd', text: '#1976d2' };
      case NodeStatus.COMPLETED:
        return { border: '#4caf50', bg: '#e8f5e9', text: '#388e3c' };
      case NodeStatus.FAILED:
        return { border: '#f44336', bg: '#ffebee', text: '#d32f2f' };
      case NodeStatus.SKIPPED:
        return { border: '#9e9e9e', bg: '#f5f5f5', text: '#616161' };
      default:
        return { border: '#e0e0e0', bg: '#ffffff', text: '#666' };
    }
  };

  const colors = getStatusColor();

  return (
    <div 
      className={`execution-node ${selected ? 'selected' : ''} ${data.animation || ''}`}
      onClick={handleClick}
      style={{
        padding: '14px',
        minWidth: '220px',
        maxWidth: '280px',
        background: colors.bg,
        border: `2px solid ${colors.border}`,
        borderRadius: '10px',
        boxShadow: selected 
          ? `0 0 0 2px ${colors.border}, 0 4px 12px rgba(0,0,0,0.15)` 
          : '0 2px 6px rgba(0,0,0,0.08)',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: colors.border }} />
      
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '10px',
        marginBottom: '8px'
      }}>
        <span style={{ fontSize: '22px' }}>{getStatusIcon()}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ 
            fontWeight: 600, 
            fontSize: '14px',
            color: colors.text,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {name}
          </div>
          {duration_ms !== undefined && duration_ms > 0 && (
            <div style={{ 
              fontSize: '11px', 
              color: '#888',
              marginTop: '2px'
            }}>
              {formatDuration(duration_ms)}
            </div>
          )}
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Description */}
      {description && (
        <div style={{ 
          fontSize: '12px',
          color: '#666',
          lineHeight: 1.4,
          marginBottom: '8px'
        }}>
          {description}
        </div>
      )}

      {/* Result */}
      {result && status === NodeStatus.COMPLETED && (
        <div style={{
          marginTop: '8px',
          padding: '8px',
          background: 'rgba(76, 175, 80, 0.1)',
          borderRadius: '6px',
          fontSize: '11px',
          color: '#2e7d32',
          maxHeight: '60px',
          overflow: 'auto'
        }}>
          <div style={{ fontWeight: 500, marginBottom: '4px' }}>执行结果:</div>
          <div style={{ wordBreak: 'break-word' }}>
            {typeof result === 'string' ? result : JSON.stringify(result)}
          </div>
        </div>
      )}

      {/* Error */}
      {error && status === NodeStatus.FAILED && (
        <div style={{
          marginTop: '8px',
          padding: '8px',
          background: 'rgba(244, 67, 54, 0.1)',
          borderRadius: '6px',
          fontSize: '11px',
          color: '#c62828',
          maxHeight: '60px',
          overflow: 'auto'
        }}>
          <div style={{ fontWeight: 500, marginBottom: '4px' }}>错误信息:</div>
          <div style={{ wordBreak: 'break-word' }}>{error}</div>
        </div>
      )}

      <Handle type="source" position={Position.Right} style={{ background: colors.border }} />
    </div>
  );
};

const StatusBadge: React.FC<{ status: NodeStatus | string }> = ({ status }) => {
  const getStatusText = () => {
    switch (status) {
      case NodeStatus.PENDING:
        return '等待中';
      case NodeStatus.RUNNING:
        return '执行中';
      case NodeStatus.COMPLETED:
        return '已完成';
      case NodeStatus.FAILED:
        return '失败';
      case NodeStatus.SKIPPED:
        return '已跳过';
      default:
        return status;
    }
  };

  const getStatusStyle = () => {
    switch (status) {
      case NodeStatus.PENDING:
        return { bg: '#f5f5f5', color: '#666' };
      case NodeStatus.RUNNING:
        return { bg: '#e3f2fd', color: '#1976d2' };
      case NodeStatus.COMPLETED:
        return { bg: '#e8f5e9', color: '#388e3c' };
      case NodeStatus.FAILED:
        return { bg: '#ffebee', color: '#d32f2f' };
      case NodeStatus.SKIPPED:
        return { bg: '#f5f5f5', color: '#616161' };
      default:
        return { bg: '#f5f5f5', color: '#666' };
    }
  };

  const style = getStatusStyle();

  return (
    <span style={{
      fontSize: '10px',
      padding: '3px 8px',
      borderRadius: '4px',
      background: style.bg,
      color: style.color,
      fontWeight: 500,
      whiteSpace: 'nowrap'
    }}>
      {getStatusText()}
    </span>
  );
};

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
}
