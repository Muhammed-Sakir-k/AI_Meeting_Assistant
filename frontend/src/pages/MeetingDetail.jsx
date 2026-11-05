import React, { useState, useEffect } from 'react';
import { FileDown, Clock, Activity, Calendar, Globe, Award, Sparkles, LayoutDashboard, BrainCircuit, Users } from 'lucide-react';
import SummaryCard from '../components/SummaryCard';
import ActionItemsTable from '../components/ActionItemsTable';
import LiveTranscriptPane from '../components/LiveTranscriptPane';
import SentimentTimeline from '../components/SentimentTimeline';
import PriorityKanban from '../components/PriorityKanban';
import QuestionsLog from '../components/QuestionsLog';
import ReminderPanel from '../components/ReminderPanel';
import EmailComposer from '../components/EmailComposer';
import TranslationSwitcher from '../components/TranslationSwitcher';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

export default function MeetingDetail({ meetingId, activeSessionId, wsTranscriptSegments, liveInterimTranscript, userRole }) {
  const [activeTab, setActiveTab] = useState('overview'); // overview, analytics, tools
  const [meeting, setMeeting] = useState(null);
  const [status, setStatus] = useState({ status: 'queued', message: '' });
  const [transcript, setTranscript] = useState({ text: '', segments: [] });
  const [summary, setSummary] = useState(null);
  const [actionItems, setActionItems] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [sentiments, setSentiments] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  // Translation state
  const [selectedLang, setSelectedLang] = useState('original');
  const [originalTranscript, setOriginalTranscript] = useState(null);
  const [originalSummary, setOriginalSummary] = useState(null);

  // Poll for pipeline status if not completed/failed
  useEffect(() => {
    if (!meetingId) return;
    
    // Reset translation
    setSelectedLang('original');
    
    fetchMeetingData();
    
    let interval = null;
    const checkStatus = async () => {
      try {
        const res = await fetch(`/status/${meetingId}`);
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
          
          if (data.status === 'completed') {
            clearInterval(interval);
            fetchMeetingData(); // Reload full data
          } else if (data.status === 'failed') {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error("Failed to check status:", err);
      }
    };

    checkStatus();
    interval = setInterval(checkStatus, 3000);

    return () => clearInterval(interval);
  }, [meetingId]);

  // Handle real-time WebSocket transcript updates for active live session
  useEffect(() => {
    if (activeSessionId && wsTranscriptSegments) {
      setTranscript(prev => ({
        ...prev,
        segments: [...wsTranscriptSegments]
      }));
    }
  }, [wsTranscriptSegments, activeSessionId]);

  const fetchMeetingData = async () => {
    try {
      // Fetch meeting metadata
      const mtRes = await fetch(`/meetings/${meetingId}`);
      if (mtRes.ok) {
        const data = await mtRes.json();
        setMeeting(data);
      }

      // 1. Fetch transcript
      const trRes = await fetch(`/transcript/${meetingId}`);
      if (trRes.ok) {
        const data = await trRes.json();
        setTranscript(data);
        setOriginalTranscript(data);
      }

      // 2. Fetch summary
      const smRes = await fetch(`/summary/${meetingId}`);
      if (smRes.ok) {
        const data = await smRes.json();
        setSummary(data);
        setOriginalSummary(data);
      }

      // 3. Fetch actions
      const acRes = await fetch(`/actions/${meetingId}`);
      if (acRes.ok) {
        const data = await acRes.json();
        setActionItems(data);
      }

      // 4. Fetch reminders
      const remRes = await fetch(`/reminders/${meetingId}`);
      if (remRes.ok) {
        const data = await remRes.json();
        setReminders(data);
      }

      // 5. Fetch sentiments
      const sentRes = await fetch(`/sentiment/${meetingId}`);
      if (sentRes.ok) {
        const data = await sentRes.json();
        setSentiments(data);
      }

      // 6. Fetch questions
      const qRes = await fetch(`/questions/${meetingId}`);
      if (qRes.ok) {
        const data = await qRes.json();
        setQuestions(data);
      }

      // 7. Fetch analytics
      const anRes = await fetch(`/analytics/${meetingId}`);
      if (anRes.ok) {
        const data = await anRes.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error("Failed to fetch meeting components:", err);
    }
  };

  const handleLanguageChange = async (langCode) => {
    setSelectedLang(langCode);
    if (langCode === 'original') {
      setTranscript(originalTranscript);
      setSummary(originalSummary);
      return;
    }

    try {
      const res = await fetch(`/translate/${meetingId}?target_lang=${langCode}`);
      if (res.ok) {
        const data = await res.json();
        
        // Map translated text to transcript segments (just split or display as unified translated blocks)
        setTranscript(prev => ({
          ...prev,
          text: data.translated_transcript,
          segments: [{ id: 0, start: 0, text: data.translated_transcript, confidence: 1.0 }]
        }));
        
        setSummary(prev => ({
          ...prev,
          summary_text: data.translated_summary,
          executive_summary: data.translated_summary.slice(0, 200)
        }));
      }
    } catch (err) {
      console.error("Translation request failed:", err);
    }
  };

  const handleStatusToggle = (actionId, newStatus) => {
    setActionItems(prev => prev.map(item => 
      item.action_id === actionId ? { ...item, status: newStatus } : item
    ));
    
    // Refresh analytics metric
    setTimeout(fetchMeetingData, 1000);
  };

  const handleReminderUpdate = (reminderId, newStatus) => {
    setReminders(prev => prev.map(r =>
      r.reminder_id === reminderId ? { ...r, status: newStatus } : r
    ));
  };

  const downloadReport = (format) => {
    window.open(`/report/${meetingId}?format=${format}`, '_blank');
  };

  const getStatusPercent = () => {
    const s = status.status;
    if (s === 'queued') return 10;
    if (s === 'preprocessing') return 25;
    if (s === 'transcribing') return 50;
    if (s === 'nlp_extraction') return 75;
    if (s === 'summarizing') return 90;
    if (s === 'completed') return 100;
    return 0; // failed or unknown
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const isPipelineActive = ['queued', 'preprocessing', 'transcribing', 'nlp_extraction', 'summarizing'].includes(status.status);

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0b0f19] overflow-y-auto">
      {/* Top Banner Pipeline Status */}
      {isPipelineActive && (
        <div className="bg-primary-600/10 border-b border-primary-500/20 py-2.5 px-6 flex items-center justify-between text-xs text-primary-400 font-semibold gap-4 animate-pulse">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-500 pulse-active inline-block"></span>
            <span>{status.message || "Running meeting processing pipeline..."}</span>
          </div>
          <div className="w-48 bg-slate-900 border border-white/5 h-2 rounded-full overflow-hidden">
            <div className="bg-primary-600 h-full transition-all duration-500" style={{ width: `${getStatusPercent()}%` }}></div>
          </div>
        </div>
      )}

      {/* Main Header */}
      <header className="px-6 py-6 border-b border-white/5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white/[0.005]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 mb-1.5">{meeting?.title || "Meeting Session"}</h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Calendar size={13} className="text-slate-500" />
              <span>{formatDate(meeting?.date)}</span>
            </span>
            <span className="flex items-center gap-1.5 border-l border-white/5 pl-4">
              <Globe size={13} className="text-slate-500" />
              <span className="uppercase">{meeting?.language || "en"}</span>
            </span>
            {meeting?.duration_seconds > 0 && (
              <span className="flex items-center gap-1.5 border-l border-white/5 pl-4">
                <Clock size={13} className="text-slate-500" />
                <span>{Math.floor(meeting.duration_seconds / 60)}m {meeting.duration_seconds % 60}s</span>
              </span>
            )}
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center gap-3 self-end lg:self-auto">
          {/* Translation Dropdown */}
          <TranslationSwitcher activeLanguage={selectedLang} onLanguageChange={handleLanguageChange} />

          {/* Export PDF */}
          <button
            onClick={() => downloadReport('pdf')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-900 border border-white/5 hover:border-white/10 rounded-lg text-slate-300 transition duration-200"
          >
            <FileDown size={13} />
            <span>PDF</span>
          </button>

          {/* Export Word */}
          <button
            onClick={() => downloadReport('docx')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-900 border border-white/5 hover:border-white/10 rounded-lg text-slate-300 transition duration-200"
          >
            <FileDown size={13} />
            <span>Word</span>
          </button>
        </div>
      </header>

      {/* Tabs Selector */}
      <div className="px-6 border-b border-white/5 bg-slate-950/20 flex gap-6">
        {[
          { id: 'overview', name: 'Meeting Overview', icon: LayoutDashboard },
          { id: 'analytics', name: 'Intelligence & Charts', icon: BrainCircuit },
          { id: 'tools', name: 'Productivity Tools', icon: Users }
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-4 font-semibold text-xs border-b-2 transition outline-none ${
                isActive 
                  ? 'border-primary-500 text-primary-400 font-bold' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon size={14} />
              <span>{tab.name}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="flex-1 p-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            {/* Left: Summaries */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              <SummaryCard summary={summary} />
              <LiveTranscriptPane transcript={transcript} liveTranscript={liveInterimTranscript} />
            </div>

            {/* Right: Actions */}
            <div className="flex flex-col gap-6">
              <ActionItemsTable actionItems={actionItems} onStatusToggle={handleStatusToggle} meetingId={meetingId} userRole={userRole} />
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="flex flex-col gap-6">
            <AnalyticsDashboard analytics={analytics} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SentimentTimeline sentimentData={sentiments} />
              <PriorityKanban actionItems={actionItems} />
            </div>
          </div>
        )}

        {activeTab === 'tools' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            <div className="lg:col-span-2 flex flex-col gap-6">
              <EmailComposer meetingId={meetingId} actionItems={actionItems} userRole={userRole} />
            </div>
            <div className="flex flex-col gap-6">
              <QuestionsLog questions={questions} />
              <ReminderPanel reminders={reminders} onReminderUpdate={handleReminderUpdate} meetingId={meetingId} userRole={userRole} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
