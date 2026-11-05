import React, { useState } from 'react';
import { ListChecks, CheckCircle2, Circle, AlertTriangle, AlertCircle, Clock } from 'lucide-react';

export default function ActionItemsTable({ actionItems, onStatusToggle, meetingId, userRole }) {
  const [filterOwner, setFilterOwner] = useState('All');
  const [filterStatus, setFilterStatus] = useState('All');
  
  const isAdmin = userRole === 'admin';

  // Extract unique owners for filter dropdown
  const owners = ['All', ...new Set(actionItems.map(item => item.owner || 'Unassigned'))];

  const handleStatusClick = async (actionId, currentStatus) => {
    if (!isAdmin) return;
    const nextStatus = currentStatus === 'done' ? 'pending' : 'done';
    try {
      const res = await fetch(`/actions/${meetingId}/${actionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus })
      });
      if (res.ok) {
        onStatusToggle(actionId, nextStatus);
      }
    } catch (err) {
      console.error("Failed to update action status:", err);
    }
  };

  const filteredItems = actionItems.filter(item => {
    const ownerMatch = filterOwner === 'All' || (item.owner || 'Unassigned') === filterOwner;
    const statusMatch = filterStatus === 'All' || item.status === filterStatus;
    return ownerMatch && statusMatch;
  });

  const getPriorityBadgeColor = (priority) => {
    const p = (priority || 'medium').toLowerCase();
    if (p === 'high') return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
    if (p === 'low') return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
  };

  return (
    <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl overflow-hidden flex flex-col h-full">
      {/* Table Header & Filters */}
      <div className="px-5 py-4 border-b border-white/5 bg-white/[0.01] flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="bg-primary-500/10 p-2 rounded-lg text-primary-400">
            <ListChecks size={18} />
          </div>
          <h3 className="font-semibold text-slate-100">Action Items</h3>
        </div>
        
        {/* Filters */}
        <div className="flex items-center gap-2">
          {/* Owner Filter */}
          <select
            value={filterOwner}
            onChange={(e) => setFilterOwner(e.target.value)}
            className="text-xs bg-slate-900 border border-white/5 text-slate-300 rounded px-2 py-1 outline-none focus:border-primary-500 transition duration-200"
          >
            {owners.map(o => (
              <option key={o} value={o}>Owner: {o}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-slate-900 border border-white/5 text-slate-300 rounded px-2 py-1 outline-none focus:border-primary-500 transition duration-200"
          >
            <option value="All">Status: All</option>
            <option value="pending">Pending</option>
            <option value="done">Completed</option>
          </select>
        </div>
      </div>

      {/* Table Content */}
      <div className="flex-1 overflow-x-auto min-h-[220px]">
        {filteredItems.length === 0 ? (
          <div className="text-slate-500 text-sm italic py-10 text-center flex flex-col items-center justify-center gap-2">
            <CheckCircle2 size={32} className="text-slate-600" />
            <span>No action items match the selected filter.</span>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-white/[0.005]">
                <th className="py-3 px-4 w-12 text-center">Done</th>
                <th className="py-3 px-4">Owner</th>
                <th className="py-3 px-4">Task Description</th>
                <th className="py-3 px-4 w-28">Deadline</th>
                <th className="py-3 px-4 w-24 text-center">Priority</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => {
                const isCompleted = item.status === 'done';
                return (
                  <tr 
                    key={item.action_id} 
                    className={`border-b border-white/5 text-sm transition duration-150 hover:bg-white/[0.015] ${
                      isCompleted ? 'opacity-60 bg-white/[0.002]' : ''
                    }`}
                  >
                    {/* Status Checkbox */}
                    <td className="py-3.5 px-4 text-center">
                      <button
                        onClick={() => isAdmin && handleStatusClick(item.action_id, item.status)}
                        disabled={!isAdmin}
                        className={`transition-colors duration-200 focus:outline-none ${
                          !isAdmin ? 'cursor-not-allowed text-slate-600' :
                          isCompleted ? 'text-primary-500' : 'text-slate-500 hover:text-slate-400'
                        }`}
                      >
                        {isCompleted ? (
                          <CheckCircle2 size={19} className="fill-primary-500/10" />
                        ) : (
                          <Circle size={19} />
                        )}
                      </button>
                    </td>

                    {/* Owner */}
                    <td className="py-3.5 px-4 font-semibold text-slate-200 whitespace-nowrap">
                      {item.owner || 'Unassigned'}
                    </td>

                    {/* Task */}
                    <td className={`py-3.5 px-4 text-slate-300 leading-relaxed max-w-xs md:max-w-md ${isCompleted ? 'line-through text-slate-500' : ''}`}>
                      {item.task}
                    </td>

                    {/* Deadline */}
                    <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">
                      <div className="flex items-center gap-1.5 text-xs">
                        <Clock size={12} className="text-slate-500" />
                        <span>{item.deadline || 'No deadline'}</span>
                      </div>
                    </td>

                    {/* Priority */}
                    <td className="py-3.5 px-4 text-center">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full inline-block uppercase tracking-wider ${getPriorityBadgeColor(item.priority)}`}>
                        {item.priority || 'medium'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
