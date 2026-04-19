import { useState, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';
import { X, Plus, Layers, Globe, Code2, LayoutDashboard, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ToolItem } from './ToolDock';
import { WebBrowser } from './WebBrowser';
import { IDE } from './IDE';
import { AdapterDefault } from './AdapterDefault';

// ============ 类型定义 ============

interface VisualAdapterProps {
  droppedItems: ToolItem[];
  onItemUse?: (item: ToolItem, target: 'thinking' | 'execution') => void;
  onEdit?: (item: ToolItem) => void;
}

export type TabType = 'canvas' | 'web' | 'ide' | 'default';

export interface TabInfo {
  id: string;
  label: string;
  type: TabType;
  closable: boolean;
}

// ============ Vis节点组件 ============

interface VisNodeProps {
  data: {
    item: ToolItem;
    onClick: () => void;
  };
}

function VisNodeComponent({ data }: VisNodeProps) {
  const { item, onClick } = data;
  const Icon = item.icon;

  return (
    <div
      onClick={onClick}
      className={cn(
        "w-[140px] rounded-xl border-2 cursor-pointer transition-all duration-200 overflow-hidden",
        "hover:scale-105 hover:shadow-xl"
      )}
      style={{ borderColor: item.color, backgroundColor: `${item.color}20` }}
    >
      <div
        className="px-3 py-2 flex items-center gap-2"
        style={{ backgroundColor: item.color }}
      >
        <Icon className="w-4 h-4 text-slate-900" />
        <span className="text-xs font-medium text-slate-900 truncate">{item.name}</span>
      </div>
      <div className="p-2">
        <span className={cn(
          "text-[10px] px-1.5 py-0.5 rounded",
          item.type === 'mcp' && "bg-blue-500/30 text-blue-200",
          item.type === 'skill' && "bg-purple-500/30 text-purple-200",
          item.type === 'setting' && "bg-green-500/30 text-green-200",
          item.type === 'file' && "bg-orange-500/30 text-orange-200"
        )}>
          {item.type.toUpperCase()}
        </span>
        <p className="text-[10px] text-white/60 mt-1 line-clamp-2">{item.description}</p>
      </div>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  visNode: VisNodeComponent,
};

// ============ 新建标签页对话框 ============

function NewTabDialog({
  isOpen,
  onClose,
  onCreate
}: {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, type: TabType) => void;
}) {
  const [name, setName] = useState('');
  const [selectedType, setSelectedType] = useState<TabType>('default');

  if (!isOpen) return null;

  const typeOptions: { type: TabType; label: string; icon: React.ElementType; desc: string }[] = [
    { type: 'default', label: 'Adapter', icon: LayoutDashboard, desc: '任务详情与进度面板' },
    { type: 'web', label: 'Web浏览器', icon: Globe, desc: '内嵌浏览器' },
    { type: 'ide', label: 'IDE', icon: Code2, desc: '代码编辑器' },
    { type: 'canvas', label: '画布', icon: Layers, desc: '可视化画布' },
  ];

  const handleCreate = () => {
    if (name.trim()) {
      onCreate(name.trim(), selectedType);
      setName('');
      setSelectedType('default');
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-600 rounded-2xl p-6 w-[420px] shadow-2xl">
        <h3 className="text-lg font-semibold text-white mb-1">新建 Adapter 标签页</h3>
        <p className="text-sm text-slate-400 mb-4">输入名称并选择类型</p>

        {/* 名称输入 */}
        <div className="mb-4">
          <label className="text-xs text-slate-400 mb-1.5 block">标签页名称</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            placeholder="例如: 任务监控、浏览器、编辑器..."
            className="w-full px-3 py-2.5 bg-slate-700/80 border border-slate-600 rounded-lg text-sm text-white placeholder:text-slate-500 outline-none focus:border-blue-500 transition-colors"
            autoFocus
          />
        </div>

        {/* 类型选择 */}
        <div className="mb-6">
          <label className="text-xs text-slate-400 mb-2 block">页面类型</label>
          <div className="grid grid-cols-2 gap-2">
            {typeOptions.map(opt => {
              const Icon = opt.icon;
              return (
                <button
                  key={opt.type}
                  onClick={() => setSelectedType(opt.type)}
                  className={cn(
                    "flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-left transition-all",
                    selectedType === opt.type
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-slate-600 bg-slate-700/30 hover:border-slate-500"
                  )}
                >
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                    selectedType === opt.type ? "bg-blue-500/20" : "bg-slate-600/30"
                  )}>
                    <Icon className={cn(
                      "w-4 h-4",
                      selectedType === opt.type ? "text-blue-400" : "text-slate-400"
                    )} />
                  </div>
                  <div>
                    <div className={cn(
                      "text-xs font-medium",
                      selectedType === opt.type ? "text-blue-300" : "text-slate-300"
                    )}>
                      {opt.label}
                    </div>
                    <div className="text-[10px] text-slate-500">{opt.desc}</div>
                  </div>
                  {selectedType === opt.type && (
                    <Check className="w-3.5 h-3.5 text-blue-400 ml-auto flex-shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* 按钮 */}
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={!name.trim()}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              name.trim()
                ? "bg-blue-600 hover:bg-blue-500 text-white"
                : "bg-slate-600 text-slate-400 cursor-not-allowed"
            )}
          >
            创建
          </button>
        </div>
      </div>
    </div>
  );
}

// ============ 画布页面组件 ============

function CanvasPage({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  handleDragOver,
  handleDrop,
}: {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
  handleDragOver: (e: React.DragEvent) => void;
  handleDrop: (e: React.DragEvent) => void;
}) {
  return (
    <div className="flex-1 relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
        className="w-full h-full"
      >
        <Background color="#ffffff30" gap={20} size={1} />
        <Controls className="bg-slate-800/80 border border-white/20" />
      </ReactFlow>

      {/* 拖放覆盖层 */}
      <div
        className="absolute inset-0 z-50"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{ pointerEvents: 'auto' }}
      />

      {/* 空状态提示 */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-40">
          <div className="text-center text-white/30">
            <Layers className="w-16 h-16 mx-auto mb-3" />
            <p className="text-sm">拖拽工具到此处</p>
            <p className="text-xs mt-1">或点击左侧工具栏图标</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ============ 主组件 ============

export function VisualAdapter({ onEdit }: VisualAdapterProps) {
  // ReactFlow状态
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, , onEdgesChange] = useEdgesState<Edge>([]);

  // 标签页状态
  const [tabs, setTabs] = useState<TabInfo[]>([
    { id: 'canvas', label: '画布', type: 'canvas', closable: false },
    { id: 'web', label: 'Web', type: 'web', closable: false },
    { id: 'ide', label: 'IDE', type: 'ide', closable: false },
  ]);
  const [activeTabId, setActiveTabId] = useState('canvas');
  const [showNewTabDialog, setShowNewTabDialog] = useState(false);

  // 处理拖放
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = 'copy';
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    let data = e.dataTransfer.getData('application/json');
    if (!data) {
      const types = e.dataTransfer.types;
      for (const type of types) {
        if (type === 'application/json' || type === 'text/plain') {
          data = e.dataTransfer.getData(type);
          break;
        }
      }
    }

    if (data) {
      try {
        const item: ToolItem = JSON.parse(data);
        const newNode: Node = {
          id: `${item.id}-${Date.now()}`,
          type: 'visNode',
          position: {
            x: 50 + Math.random() * 200,
            y: 50 + Math.random() * 150
          },
          data: {
            item,
            onClick: () => onEdit?.(item)
          },
        };
        setNodes(prev => [...prev, newNode]);
        onEdit?.(item);
      } catch (err) {
        console.error('Drop error:', err);
      }
    }
  }, [onEdit, setNodes]);

  // 创建新标签页
  const handleCreateTab = useCallback((name: string, type: TabType) => {
    const newTab: TabInfo = {
      id: `tab-${Date.now()}`,
      label: name,
      type,
      closable: true,
    };
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newTab.id);
  }, []);

  // 关闭标签页
  const handleCloseTab = useCallback((tabId: string) => {
    setTabs(prev => {
      const newTabs = prev.filter(t => t.id !== tabId);
      if (newTabs.length > 0) {
        setActiveTabId(newTabs[newTabs.length - 1].id);
      }
      return newTabs;
    });
  }, []);

  // 获取当前激活的标签页
  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];

  // 渲染标签页图标
  const renderTabIcon = (type: TabType) => {
    switch (type) {
      case 'canvas': return <Layers className="w-3 h-3" />;
      case 'web': return <Globe className="w-3 h-3" />;
      case 'ide': return <Code2 className="w-3 h-3" />;
      case 'default': return <LayoutDashboard className="w-3 h-3" />;
      default: return <LayoutDashboard className="w-3 h-3" />;
    }
  };

  // 渲染标签页内容
  const renderTabContent = () => {
    if (!activeTab) return null;

    switch (activeTab.type) {
      case 'canvas':
        return (
          <CanvasPage
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            handleDragOver={handleDragOver}
            handleDrop={handleDrop}
          />
        );
      case 'web':
        return <WebBrowser />;
      case 'ide':
        return <IDE />;
      case 'default':
        return <AdapterDefault />;
      default:
        return <AdapterDefault />;
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-900">
      {/* ===== 顶部标签栏 ===== */}
      <div className="flex items-center gap-0.5 px-1 py-1 bg-slate-800/90 border-b border-slate-700/50 overflow-x-auto">
        {/* 固定标签页 */}
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTabId(tab.id)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-all flex-shrink-0 group",
              activeTabId === tab.id
                ? "bg-slate-700 text-white"
                : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200"
            )}
          >
            {renderTabIcon(tab.type)}
            <span className="truncate max-w-[80px]">{tab.label}</span>
            {tab.closable && (
              <X
                className={cn(
                  "w-3 h-3 rounded-full transition-colors flex-shrink-0",
                  activeTabId === tab.id
                    ? "hover:bg-red-500/20 hover:text-red-400 text-slate-400"
                    : "opacity-0 group-hover:opacity-100 hover:bg-red-500/20 hover:text-red-400"
                )}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCloseTab(tab.id);
                }}
              />
            )}
          </button>
        ))}

        {/* 新建标签页按钮 */}
        <button
          onClick={() => setShowNewTabDialog(true)}
          className="w-6 h-6 rounded-md hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors flex-shrink-0 ml-1"
          title="新建标签页"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* ===== 主内容区域 ===== */}
      <div className="flex-1 overflow-hidden">
        {renderTabContent()}
      </div>

      {/* ===== 新建标签页对话框 ===== */}
      <NewTabDialog
        isOpen={showNewTabDialog}
        onClose={() => setShowNewTabDialog(false)}
        onCreate={handleCreateTab}
      />
    </div>
  );
}
