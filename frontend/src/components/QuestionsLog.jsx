import React, { useState } from 'react';
import { HelpCircle, CheckCircle, XCircle } from 'lucide-react';

export default function QuestionsLog({ questions }) {
  const [filter, setFilter] = useState('all'); // all, answered, unanswered

  const formatTime = (seconds) => {
    if (seconds == null || isNaN(seconds)) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const filteredQuestions = questions.filter(q => {
    if (filter === 'answered') return q.status === 'answered';
    if (filter === 'unanswered') return q.status === 'unanswered';
    return true;
  });

  return (
    <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl p-5 flex flex-col h-full">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 border-b border-white/5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="bg-blue-500/10 p-2 rounded-lg text-blue-400">
            <HelpCircle size={18} />
          </div>
          <h3 className="font-semibold text-slate-100">Questions Log</h3>
        </div>

        {/* Tab Filters */}
        <div className="flex items-center bg-slate-900/60 p-0.5 rounded-lg border border-white/5">
          {['all', 'unanswered', 'answered'].map(tab => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1 text-[11px] font-semibold rounded-md transition duration-200 capitalize outline-none ${
                filter === tab
                  ? 'bg-primary-600 text-white shadow-sm shadow-primary-950/10'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto max-h-[350px] min-h-[220px] space-y-3.5 pr-1">
        {filteredQuestions.length === 0 ? (
          <div className="text-slate-500 text-xs italic py-10 text-center flex flex-col items-center justify-center gap-2">
            <HelpCircle size={28} className="text-slate-600" />
            <span>No questions found in this category.</span>
          </div>
        ) : (
          filteredQuestions.map((q) => {
            const isAnswered = q.status === 'answered';
            return (
              <div 
                key={q.question_id}
                className="p-3.5 rounded-xl bg-white/[0.015] border border-white/5 hover:border-white/10 transition-all duration-200 flex items-start justify-between gap-4"
              >
                <div className="flex flex-col gap-1.5">
                  <p className="text-[13.5px] leading-relaxed text-slate-200 font-medium">
                    "{q.question_text}"
                  </p>
                  <span className="text-[10px] font-mono text-slate-500">
                    Asked at: {formatTime(q.asked_at)}
                  </span>
                </div>

                {/* Status Badge */}
                <span className={`flex-shrink-0 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full select-none ${
                  isAnswered
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}>
                  {isAnswered ? (
                    <>
                      <CheckCircle size={10} />
                      <span>Resolved</span>
                    </>
                  ) : (
                    <>
                      <XCircle size={10} />
                      <span>Unresolved</span>
                    </>
                  )}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
