/**
 * ThinkingNode.tsx - 思考节点组件
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { ThinkingNodeData, ThinkingOptionData, NodeStatus } from '../../../core/protocol/messageTypes';

interface ThinkingNodeComponentData extends ThinkingNodeData {
  onOptionSelect?: (nodeId: string, optionId: string) => void;
  animation?: 'pulse' | 'glow' | 'none';
}

export const ThinkingNode: React.FC<NodeProps<ThinkingNodeComponentData>> = ({ 
  id, 
  data,
  selected 
}) => {
  const { question, options, selected_option, status, onOptionSelect } = data;

  const handleOptionClick = (optionId: string) => {
    if (onOptionSelect && status !== NodeStatus.SELECTED) {
      onOptionSelect(id, optionId);
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case NodeStatus.PENDING:
        return '💭';
      case NodeStatus.RUNNING:
        return '🤔';
      case NodeStatus.SELECTED:
        return '✅';
      default:
        return '💭';
    }
  };

  return (
    <div 
      className={`thinking-node ${selected ? 'selected' : ''} ${data.animation || ''}`}
      style={{
        padding: '16px',
        minWidth: '240px',
        maxWidth: '320px',
        background: '#ffffff',
        borderRadius: '12px',
        boxShadow: selected 
          ? '0 0 0 2px #2196f3, 0 4px 12px rgba(0,0,0,0.15)' 
          : '0 2px 8px rgba(0,0,0,0.1)',
        transition: 'all 0.2s ease',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: '#999' }} />
      
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px',
        marginBottom: '12px',
        paddingBottom: '8px',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <span style={{ fontSize: '20px' }}>{getStatusIcon()}</span>
        <span style={{ 
          fontWeight: 600, 
          fontSize: '14px',
          color: '#333'
        }}>思考节点</span>
        {status === NodeStatus.SELECTED && (
          <span style={{ 
            marginLeft: 'auto',
            fontSize: '12px',
            color: '#4caf50',
            background: '#e8f5e9',
            padding: '2px 8px',
            borderRadius: '4px'
          }}>已选择</span>
        )}
      </div>

      {/* Question */}
      <div style={{ 
        marginBottom: '12px',
        fontSize: '13px',
        color: '#333',
        lineHeight: 1.5
      }}>
        {question}
      </div>

      {/* Options */}
      {options && options.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {options.map((option) => (
            <OptionButton
              key={option.id}
              option={option}
              isSelected={selected_option === option.id}
              isDisabled={status === NodeStatus.SELECTED}
              onClick={() => handleOptionClick(option.id)}
            />
          ))}
        </div>
      )}

      <Handle type="source" position={Position.Right} style={{ background: '#999' }} />
    </div>
  );
};

interface OptionButtonProps {
  option: ThinkingOptionData;
  isSelected: boolean;
  isDisabled: boolean;
  onClick: () => void;
}

const OptionButton: React.FC<OptionButtonProps> = ({ 
  option, 
  isSelected, 
  isDisabled, 
  onClick 
}) => {
  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        padding: '10px 12px',
        border: isSelected 
          ? '2px solid #4caf50' 
          : option.is_default 
            ? '2px solid #2196f3' 
            : '1px solid #e0e0e0',
        borderRadius: '8px',
        background: isSelected 
          ? '#e8f5e9' 
          : option.is_default 
            ? '#e3f2fd' 
            : '#fafafa',
        cursor: isDisabled ? 'default' : 'pointer',
        opacity: isDisabled && !isSelected ? 0.6 : 1,
        transition: 'all 0.2s ease',
        textAlign: 'left',
        width: '100%',
      }}
      onMouseEnter={(e) => {
        if (!isDisabled) {
          e.currentTarget.style.background = '#f5f5f5';
          e.currentTarget.style.borderColor = '#2196f3';
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.background = option.is_default ? '#e3f2fd' : '#fafafa';
          e.currentTarget.style.borderColor = option.is_default ? '#2196f3' : '#e0e0e0';
        }
      }}
    >
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px',
        width: '100%'
      }}>
        <span style={{ 
          fontWeight: 600, 
          fontSize: '13px',
          color: '#333'
        }}>
          [{option.id}] {option.label}
        </span>
        {option.is_default && (
          <span style={{ 
            marginLeft: 'auto',
            fontSize: '10px',
            color: '#2196f3',
            background: 'rgba(33, 150, 243, 0.1)',
            padding: '2px 6px',
            borderRadius: '4px'
          }}>推荐</span>
        )}
      </div>
      <span style={{ 
        fontSize: '11px', 
        color: '#666',
        marginTop: '4px'
      }}>
        {option.description}
      </span>
      <div style={{ 
        marginTop: '6px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px'
      }}>
        <div style={{
          width: '60px',
          height: '4px',
          background: '#e0e0e0',
          borderRadius: '2px',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${option.confidence * 100}%`,
            height: '100%',
            background: option.confidence > 0.8 ? '#4caf50' : option.confidence > 0.6 ? '#ff9800' : '#f44336',
            borderRadius: '2px'
          }} />
        </div>
        <span style={{ fontSize: '10px', color: '#999' }}>
          {Math.round(option.confidence * 100)}%
        </span>
      </div>
    </button>
  );
};
