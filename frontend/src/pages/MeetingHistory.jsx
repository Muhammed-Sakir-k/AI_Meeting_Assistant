import React, { useState, useEffect } from 'react';
import { Search, RotateCw, FolderOpen, Calendar } from 'lucide-react';

export default function MeetingHistory({ activeMeetingId, onSelectMeeting, refreshTrigger, onRefresh }) {
  const [meetings, setMeetings] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMeetings();
  }, [refreshTrigger, search]);

  const fetchMeetings = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/search?q=${encodeURIComponent(search)}`);
      if (res.ok) {
        const data = await res.json();
        // Sort by date/id descending (newest first)
        data.sort((a, b) => b.meeting_id - a.meeting_id);
        setMeetings(data);
      }
    } catch (err) {
      console.error("Failed to load meeting list:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Unknown Date";
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="flex flex-col h-full border-r border-white/5 bg-[#090d16] select-none">
      {/* Search Header */}
      <div className="p-4 border-b border-white/5 flex flex-col gap-3">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search meetings..."
            className="w-full pl-9 pr-4 py-2 bg-slate-900/60 border border-white/5 focus:border-primary-500 rounded-lg text-xs text-slate-200 outline-none transition duration-200"
          />
        </div>

        <div className="flex items-center justify-between">
          <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <FolderOpen size={10} />
            <span>Recent Meetings</span>
          </h2>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="text-slate-400 hover:text-slate-200 disabled:opacity-50 transition"
            title="Refresh history"
          >
            <RotateCw size={11} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {loading && meetings.length === 0 ? (
          <div className="text-slate-500 text-xs italic py-8 text-center flex items-center justify-center gap-1.5">
            <RotateCw size={12} className="animate-spin" />
            <span>Loading database...</span>
          </div>
        ) : meetings.length === 0 ? (
          <div className="text-slate-500 text-xs italic py-8 text-center">
            No meetings found
          </div>
        ) : (
          meetings.map((m) => {
            const isActive = m.meeting_id === activeMeetingId;
            return (
              <button
                key={m.meeting_id}
                onClick={() => onSelectMeeting(m.meeting_id)}
                className={`w-full text-left p-3 rounded-xl transition duration-200 flex flex-col gap-1 border outline-none ${
                  isActive
                    ? 'bg-primary-600/10 border-primary-500/30'
                    : 'bg-transparent border-transparent hover:bg-white/[0.01] hover:border-white/5'
                }`}
              >
                <span className={`text-xs font-semibold leading-snug truncate ${
                  isActive ? 'text-primary-400' : 'text-slate-200'
                }`}>
                  {m.title || `Meeting #${m.meeting_id}`}
                </span>
                
                <div className="flex items-center gap-2.5 text-[10px] text-slate-500">
                  <span className="flex items-center gap-1">
                    <Calendar size={10} />
                    <span>{formatDate(m.date)}</span>
                  </span>
                  <span className="bg-slate-900 px-1.5 py-0.2 rounded uppercase border border-white/5 font-mono">
                    {m.language ? m.language.toUpperCase() : 'EN'}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
