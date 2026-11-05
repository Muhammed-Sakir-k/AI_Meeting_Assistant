import React from 'react';
import { Bell, BellOff, Send, Check } from 'lucide-react';

export default function ReminderPanel({ reminders, onReminderUpdate, meetingId, userRole }) {
  const isAdmin = userRole === 'admin';

  const handleDismiss = async (reminderId) => {
    if (!isAdmin) return;
    try {
      const res = await fetch(`/reminders/${meetingId}/dismiss/${reminderId}`, {
        method: 'POST'
      });
      if (res.ok) {
        onReminderUpdate(reminderId, 'dismissed');
      }
    } catch (err) {
      console.error("Failed to dismiss reminder:", err);
    }
  };

  const handleResend = async (reminderId) => {
    if (!isAdmin) return;
    try {
      const res = await fetch(`/reminders/${meetingId}/resend/${reminderId}`, {
        method: 'POST'
      });
      if (res.ok) {
        onReminderUpdate(reminderId, 'sent');
      }
    } catch (err) {
      console.error("Failed to resend reminder:", err);
    }
  };

  const getStatusStyle = (status) => {
    const s = status.toLowerCase();
    if (s === 'sent') return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    if (s === 'dismissed') return 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
    return 'bg-amber-500/10 text-amber-400 border border-amber-500/20'; // pending
  };

  return (
    <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl p-5 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-4 border-b border-white/5 pb-3">
        <div className="bg-amber-500/10 p-2 rounded-lg text-amber-400">
          <Bell size={18} />
        </div>
        <h3 className="font-semibold text-slate-100">Reminders Manager</h3>
      </div>

      {/* Reminders List */}
      <div className="flex-1 overflow-y-auto max-h-[350px] min-h-[220px] space-y-3.5 pr-1">
        {reminders.length === 0 ? (
          <div className="text-slate-500 text-xs italic py-10 text-center flex flex-col items-center justify-center gap-2">
            <BellOff size={28} className="text-slate-600" />
            <span>No reminders generated for this meeting.</span>
          </div>
        ) : (
          reminders.map((rem) => {
            const isDismissed = rem.status === 'dismissed';
            return (
              <div 
                key={rem.reminder_id}
                className={`p-3.5 rounded-xl bg-white/[0.015] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all duration-200 hover:border-white/10 ${
                  isDismissed ? 'opacity-50' : ''
                }`}
              >
                <div className="flex flex-col gap-1">
                  <p className="text-[13.5px] leading-relaxed text-slate-200 font-medium">
                    {rem.reminder_text}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500">
                      Owner: <span className="text-slate-400 font-semibold">{rem.owner_name}</span>
                    </span>
                    <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full select-none ${getStatusStyle(rem.status)}`}>
                      {rem.status}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                {!isDismissed && isAdmin && (
                  <div className="flex items-center gap-2.5 self-end sm:self-auto">
                    {/* Dismiss Button */}
                    <button
                      onClick={() => handleDismiss(rem.reminder_id)}
                      className="px-2.5 py-1 text-[11px] font-semibold bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded border border-white/5 flex items-center gap-1 transition duration-200"
                      title="Dismiss reminder"
                    >
                      <Check size={11} />
                      <span>Dismiss</span>
                    </button>
                    {/* Resend Button */}
                    <button
                      onClick={() => handleResend(rem.reminder_id)}
                      className="px-2.5 py-1 text-[11px] font-semibold bg-primary-600 hover:bg-primary-500 text-white rounded flex items-center gap-1 transition duration-200"
                      title="Resend notification"
                    >
                      <Send size={11} />
                      <span>Send Now</span>
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
