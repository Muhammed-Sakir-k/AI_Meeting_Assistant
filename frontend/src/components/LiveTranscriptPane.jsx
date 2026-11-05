import React, { useEffect, useRef } from 'react';
import { FileText, AlertCircle, Volume2 } from 'lucide-react';

export default function LiveTranscriptPane({ transcript, liveTranscript }) {
  const paneEndRef = useRef(null);

  // Auto-scroll transcript container on new segments or live interim speech
  useEffect(() => {
    if (paneEndRef.current) {
      paneEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [transcript, liveTranscript]);

  const segments = transcript?.segments || [];
  const confidence = transcript?.confidence_score || "1.0";
  const language = (transcript?.language || "en").toUpperCase();

  const formatTime = (seconds) => {
    if (seconds == null || isNaN(seconds)) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="card flex flex-col h-full glass-panel rounded-2xl border border-white/5 shadow-2xl overflow-hidden">
      {/* Pane Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-white/[0.01]">
        <div className="flex items-center gap-2.5">
          <div className="bg-primary-500/10 p-2 rounded-lg text-primary-400">
            <FileText size={18} />
          </div>
          <h3 className="font-semibold text-slate-100">Interactive Transcript</h3>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-white/5 font-mono">LANG: {language}</span>
          <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-white/5 font-mono">CONF: {Math.round(parseFloat(confidence) * 100)}%</span>
        </div>
      </div>

      {/* Pane Content */}
      <div className="flex-1 p-5 overflow-y-auto min-h-[300px] max-h-[500px] flex flex-col gap-4">
        {segments.length === 0 && !liveTranscript && (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-2 py-10">
            <Volume2 size={36} className="text-slate-600 animate-pulse" />
            <p className="text-sm">No speech transcript available yet.</p>
          </div>
        )}

        {segments.map((seg, idx) => {
          const isLowConfidence = seg.is_low_confidence || (seg.confidence && parseFloat(seg.confidence) < 0.75);
          return (
            <div 
              key={seg.id || idx} 
              className={`group flex items-start gap-4 p-3.5 rounded-xl transition-all duration-200 border ${
                isLowConfidence 
                  ? 'bg-amber-500/[0.03] border-amber-500/20 hover:bg-amber-500/[0.05]' 
                  : 'bg-white/[0.01] border-transparent hover:bg-white/[0.02] hover:border-white/5'
              }`}
            >
              {/* Timestamp */}
              <span className="text-xs font-mono font-semibold text-slate-500 mt-1 select-none">
                {formatTime(seg.start)}
              </span>

              {/* Text */}
              <div className="flex-1 flex flex-col gap-1">
                <p className={`text-[14.5px] leading-relaxed ${isLowConfidence ? 'text-amber-200 font-medium' : 'text-slate-300'}`}>
                  {seg.speaker && (
                    <span className="font-bold text-primary-400 mr-2 bg-primary-500/10 px-1.5 py-0.5 rounded border border-primary-500/10 select-none">
                      {seg.speaker}
                    </span>
                  )}
                  {seg.text}
                </p>
                {isLowConfidence && (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-500 select-none mt-1">
                    <AlertCircle size={10} />
                    <span>Low transcription confidence ({Math.round(parseFloat(seg.confidence) * 100)}%) — review recommended</span>
                  </span>
                )}
              </div>
            </div>
          );
        })}

        {/* Live Interim Transcript */}
        {liveTranscript && (
          <div className="flex items-start gap-4 p-3.5 rounded-xl bg-primary-500/[0.02] border border-primary-500/10">
            <span className="text-xs font-mono font-semibold text-primary-400 mt-1 select-none animate-pulse">
              Live
            </span>
            <p className="text-[14.5px] leading-relaxed text-slate-400 italic">
              {liveTranscript}...
            </p>
          </div>
        )}

        <div ref={paneEndRef} />
      </div>

      {/* Legend Footer */}
      <div className="px-5 py-2.5 bg-slate-900/30 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded bg-amber-500/10 border border-amber-500/30 inline-block"></span>
          <span>Yellow highlight indicates low transcription confidence (&lt; 75%)</span>
        </div>
      </div>
    </div>
  );
}
