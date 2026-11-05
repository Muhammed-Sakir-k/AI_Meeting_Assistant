import React, { useState } from 'react';
import { Sparkles, Gavel, FileText } from 'lucide-react';

export default function SummaryCard({ summary }) {
  const [activeTab, setActiveTab] = useState('executive'); // executive, detailed, decisions

  const execSummary = summary?.executive_summary || "No executive summary available.";
  const detailedSummary = summary?.summary_text || "No detailed summary available.";
  const keyDecisions = summary?.key_decisions || [];

  const tabs = [
    { id: 'executive', name: 'Executive Summary', icon: Sparkles },
    { id: 'detailed', name: 'Detailed Analysis', icon: FileText },
    { id: 'decisions', name: 'Key Decisions', icon: Gavel },
  ];

  return (
    <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl overflow-hidden flex flex-col h-full">
      {/* Tabs Header */}
      <div className="flex border-b border-white/5 bg-white/[0.01]">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 font-semibold text-xs transition-all duration-300 border-b-2 outline-none ${
                isActive
                  ? 'border-primary-500 text-primary-400 bg-primary-500/[0.02]'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.01]'
              }`}
            >
              <Icon size={14} className={isActive ? 'text-primary-400' : 'text-slate-400'} />
              <span>{tab.name}</span>
            </button>
          );
        })}
      </div>

      {/* Content Body */}
      <div className="flex-1 p-6 max-h-[400px] overflow-y-auto min-h-[220px]">
        {activeTab === 'executive' && (
          <div className="space-y-3">
            <p className="text-slate-300 text-[14.5px] leading-relaxed font-normal">
              {execSummary}
            </p>
          </div>
        )}

        {activeTab === 'detailed' && (
          <div className="space-y-4">
            {detailedSummary.split('\n\n').map((para, idx) => (
              <p key={idx} className="text-slate-300 text-[14.5px] leading-relaxed font-normal">
                {para}
              </p>
            ))}
          </div>
        )}

        {activeTab === 'decisions' && (
          <div className="space-y-3">
            {keyDecisions.length === 0 ? (
              <div className="text-slate-500 text-sm italic py-4 text-center">
                No major decisions were flagged in this meeting.
              </div>
            ) : (
              <ul className="space-y-3.5">
                {keyDecisions.map((dec, idx) => (
                  <li key={idx} className="flex items-start gap-3 group">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold mt-0.5 select-none">
                      {idx + 1}
                    </span>
                    <p className="text-slate-300 text-[14px] leading-relaxed font-medium">
                      {dec}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
