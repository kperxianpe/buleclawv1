/**
 * InterventionNode.tsx - 干预节点组件
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { InterventionActionData } from '../../../core/protocol/messageTypes';

interface InterventionNodeData {
  stepId: string;
  actions: InterventionActionData[];
  onAction?: (stepId: string, actionType: string) => void;
}

export const InterventionNode: React.FC<NodeProps<InterventionNodeData>> = ({ 
  id, 
  data,
  selected 
}) => {
  const { stepId, actions, onAction } = data;

  const handleAction = (actionType: string) => {
    onAction?.(stepId, actionType);
  };

  return (
    <div 
      className={`intervention-node ${selected ? 'selected' : ''}`}
      style={{
        padding: '16px',
        minWidth: '200px',
        maxWidth: '260px',
        background: '#fff3e0',
        border: '2px solid #ff9800',
        borderRadius: '12px',
        boxShadow: selected 
          ? '0 0 0 2px #ff9800, 0 4px 12px rgba(0,0,0,0.15)' 
          : '0 2px 8px rgba(0,0,0,0.1)',
        transition: 'all 0.2s ease',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: '#ff9800' }} />
      
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px',
        marginBottom: '12px',
        paddingBottom: '8px',
        borderBottom: '1px solid rgba(255, 152, 0, 0.2)'
      }}>
        <span style={{ fontSize: '20px' }}>⚠️</span>
        <span style={{ 
          fontWeight: 600, 
          fontSize: '14px',
          color: '#e65100'
        }}>需要干预</span>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {actions.map((action) => (
          <ActionButton
            key={action.type}
            action={action}
            onClick={() => handleAction(action.type)}
          />
        ))}
      </div>

      <Handle type="source" position={Position.Right} style={{ background: '#ff9800' }} />
    </div>
  );
};

interface ActionButtonProps {
  action: InterventionActionData;
  onClick: () => void;
}

const ActionButton: React.FC<ActionButtonProps> = ({ action, onClick }) => {
  const getIcon = () => {
    switch (action.type) {
      case 'retry':
        return '🔄';
      case 'skip':
        return '⏭️';
      case 'replan':
        return '📝';
      case 'stop':
        return '🛑';
      default:
        return '▶️';
    }
  };

  const getColor = () => {
    switch (action.type) {
      case 'retry':
        return { border: '#4caf50', bg: '#e8f5e9', hover: '#c8e6c9' };
      case 'skip':
        return { border: '#ff9800', bg: '#fff3e0', hover: '#ffe0b2' };
      case 'replan':
        return { border: '#2196f3', bg: '#e3f2fd', hover: '#bbdefb' };
      case 'stop':
        return { border: '#f44336', bg: '#ffebee', hover: '#ffcdd2' };
      default:
        return { border: '#e0e0e0', bg: '#f5f5f5', hover: '#eeeeee' };
    }
  };

  const colors = getColor();

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '10px 12px',
        border: `1px solid ${colors.border}`,
        borderRadius: '8px',
        background: colors.bg,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        textAlign: 'left',
        width: '100%',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = colors.hover;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = colors.bg;
      }}
    >
      <span style={{ fontSize: '16px' }}>{getIcon()}</span>
      <div style={{ flex: 1 }}>
        <div style={{ 
          fontWeight: 500, 
          fontSize: '13px',
          color: '#333'
        }}>
          {action.label}
        </div>
        <div style={{ 
          fontSize: '11px', 
          color: '#666',
          marginTop: '2px'
        }}>
          {action.description}
        </div>
      </div>
    </button>
  );
};
