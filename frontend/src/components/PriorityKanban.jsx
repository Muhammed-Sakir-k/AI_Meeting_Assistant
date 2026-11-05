import React from 'react';
import { Kanban, AlertCircle, ArrowUpRight, ArrowDownRight, RefreshCcw } from 'lucide-react';

export default function PriorityKanban({ actionItems }) {
  // Group action items by priority
  const highTasks = actionItems.filter(item => (item.priority || 'medium').toLowerCase() === 'high');
  const mediumTasks = actionItems.filter(item => (item.priority || 'medium').toLowerCase() === 'medium');
  const lowTasks = actionItems.filter(item => (item.priority || 'medium').toLowerCase() === 'low');

  const TaskCard = ({ item }) => (
    <div className={`p-4 rounded-xl glass-card border border-white/5 shadow-md flex flex-col gap-2.5 transition duration-200 hover:border-white/10 hover:shadow-lg ${
      item.status === 'done' ? 'opacity-50 border-dashed bg-white/[0.005]' : 'bg-white/[0.015]'
    }`}>
      {/* Title/Description */}
      <p className={`text-[13.5px] leading-relaxed text-slate-200 ${item.status === 'done' ? 'line-through text-slate-500 font-normal' : 'font-medium'}`}>
        {item.task}
      </p>

      {/* Footer Info */}
      <div className="flex items-center justify-between mt-1 text-[11px] border-t border-white/5 pt-2">
        <span className="font-semibold text-slate-300">
          Owner: <span className="text-slate-100">{item.owner || 'Unassigned'}</span>
        </span>
        <span className="text-slate-400 bg-slate-900/60 px-1.5 py-0.5 rounded border border-white/5">
          {item.deadline || 'No deadline'}
        </span>
      </div>
    </div>
  );

  return (
    <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl p-5 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5 border-b border-white/5 pb-3">
        <div className="bg-primary-500/10 p-2 rounded-lg text-primary-400">
          <Kanban size={18} />
        </div>
        <h3 className="font-semibold text-slate-100">Priority Kanban Board</h3>
      </div>

      {/* Board Columns Grid */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-[300px]">
        {/* High Column */}
        <div className="bg-rose-500/[0.01] border border-rose-500/10 rounded-xl p-3.5 flex flex-col h-full min-h-[150px]">
          <div className="flex items-center justify-between mb-3.5 pb-2 border-b border-rose-500/10">
            <span className="text-xs font-bold text-rose-400 tracking-wider uppercase flex items-center gap-1.5">
              <AlertCircle size={14} />
              <span>High Priority</span>
            </span>
            <span className="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full font-bold">
              {highTasks.length}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 max-h-[380px] pr-1">
            {highTasks.length === 0 ? (
              <div className="text-slate-500 text-xs italic py-6 text-center">No high priority tasks.</div>
            ) : (
              highTasks.map(task => <TaskCard key={task.action_id} item={task} />)
            )}
          </div>
        </div>

        {/* Medium Column */}
        <div className="bg-amber-500/[0.01] border border-amber-500/10 rounded-xl p-3.5 flex flex-col h-full min-h-[150px]">
          <div className="flex items-center justify-between mb-3.5 pb-2 border-b border-amber-500/10">
            <span className="text-xs font-bold text-amber-400 tracking-wider uppercase flex items-center gap-1.5">
              <ArrowUpRight size={14} />
              <span>Medium Priority</span>
            </span>
            <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full font-bold">
              {mediumTasks.length}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 max-h-[380px] pr-1">
            {mediumTasks.length === 0 ? (
              <div className="text-slate-500 text-xs italic py-6 text-center">No medium priority tasks.</div>
            ) : (
              mediumTasks.map(task => <TaskCard key={task.action_id} item={task} />)
            )}
          </div>
        </div>

        {/* Low Column */}
        <div className="bg-emerald-500/[0.01] border border-emerald-500/10 rounded-xl p-3.5 flex flex-col h-full min-h-[150px]">
          <div className="flex items-center justify-between mb-3.5 pb-2 border-b border-emerald-500/10">
            <span className="text-xs font-bold text-emerald-400 tracking-wider uppercase flex items-center gap-1.5">
              <ArrowDownRight size={14} />
              <span>Low Priority</span>
            </span>
            <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full font-bold">
              {lowTasks.length}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 max-h-[380px] pr-1">
            {lowTasks.length === 0 ? (
              <div className="text-slate-500 text-xs italic py-6 text-center">No low priority tasks.</div>
            ) : (
              lowTasks.map(task => <TaskCard key={task.action_id} item={task} />)
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
