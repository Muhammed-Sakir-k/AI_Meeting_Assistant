import React, { useEffect, useState } from 'react';
import { Command } from 'lucide-react';

export default function VoiceCommandBar({ lastCommand }) {
  const [visible, setVisible] = useState(false);
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    if (lastCommand) {
      setVisible(true);
      setFlash(true);
      
      const timer = setTimeout(() => {
        setFlash(false);
      }, 500);

      // Keep it visible for 8 seconds
      const hideTimer = setTimeout(() => {
        setVisible(false);
      }, 8000);

      return () => {
        clearTimeout(timer);
        clearTimeout(hideTimer);
      };
    }
  }, [lastCommand]);

  if (!visible || !lastCommand) return null;

  const isSuccess = lastCommand.action && lastCommand.action !== 'not_recognized' && lastCommand.action !== 'unsupported_language';

  return (
    <div className={`fixed bottom-6 right-6 z-50 glass-panel border rounded-xl py-3 px-4 shadow-xl flex items-center gap-3 transition-all duration-300 transform translate-y-0 scale-100 ${
      flash ? 'border-primary-500 bg-primary-950/20' : 'border-white/10'
    }`}>
      {/* Icon */}
      <div className={`p-1.5 rounded-lg ${
        isSuccess ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
      }`}>
        <Command size={14} className={isSuccess ? 'animate-pulse' : ''} />
      </div>

      {/* Message Info */}
      <div className="flex flex-col gap-0.5">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Voice Control</span>
        <span className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
          <span>{lastCommand.message}</span>
          {lastCommand.payload && lastCommand.payload.raw_input && (
            <span className="text-[10px] text-slate-500 italic">("{lastCommand.payload.raw_input}")</span>
          )}
        </span>
      </div>
    </div>
  );
}
