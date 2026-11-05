import React, { useState, useEffect } from 'react';
import { Sparkles, Activity, FileVideo, LayoutDashboard, UploadCloud, FileAudio, Settings, AlertCircle, XCircle } from 'lucide-react';
import MeetingHistory from './pages/MeetingHistory';
import MeetingDetail from './pages/MeetingDetail';
import AnalyticsOverview from './pages/AnalyticsOverview';
import LiveDetectionToggle from './components/LiveDetectionToggle';
import VoiceCommandBar from './components/VoiceCommandBar';
import Login from './pages/Login';
import { LogOut, ShieldAlert } from 'lucide-react';

export default function App() {
  const [user, setUser] = useState(null); // { username, role }
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, analytics
  const [activeMeetingId, setActiveMeetingId] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // File Upload states
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [uploadStatus, setUploadStatus] = useState({ type: '', message: '' });
  const [uploading, setUploading] = useState(false);

  // Live session WebSocket states
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [wsTranscriptSegments, setWsTranscriptSegments] = useState([]);
  const [liveInterimTranscript, setLiveInterimTranscript] = useState('');
  const [lastVoiceCommand, setLastVoiceCommand] = useState(null);

  // Handle file select
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setUploadStatus({ type: '', message: '' });
    }
  };

  // Trigger refresh of sidebar list
  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  // Submit audio upload form
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadStatus({ type: 'info', message: 'Uploading audio file...' });

    const formData = new FormData();
    formData.append('file', file);
    if (title.trim()) {
      formData.append('title', title.trim());
    }

    try {
      const res = await fetch('/upload', {
        method: 'POST',
        body: formData
      });

      // Handle duplicate upload (409 Conflict)
      if (res.status === 409) {
        const data = await res.json();
        setUploadStatus({ type: 'warning', message: 'Duplicate upload detected. Loading existing records.' });
        setActiveMeetingId(data.meeting_id);
        setActiveTab('dashboard');
        setFile(null);
        setTitle('');
        triggerRefresh();
        return;
      }

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed.");
      }

      const data = await res.json();
      setUploadStatus({ type: 'success', message: 'Upload completed. Pipeline initialized!' });
      
      // Auto select and start polling for new meeting
      setActiveMeetingId(data.meeting_id);
      setActiveTab('dashboard');
      
      // Reset form
      setFile(null);
      setTitle('');
      triggerRefresh();
    } catch (err) {
      setUploadStatus({ type: 'error', message: err.message || "Failed to process audio." });
    } finally {
      setUploading(false);
    }
  };

  // Live session handlers
  const handleSessionStart = (meetingId, sessionId) => {
    setActiveSessionId(sessionId);
    setActiveMeetingId(meetingId);
    setWsTranscriptSegments([]);
    setLiveInterimTranscript('');
    setActiveTab('dashboard');
    triggerRefresh();
  };

  const handleSessionStop = (meetingId) => {
    setActiveSessionId(null);
    setLiveInterimTranscript('');
    triggerRefresh();
    // Detail view will poll for status completed and reload summary/NLP data
  };

  const handleTranscriptUpdate = (msg) => {
    if (msg.is_final) {
      setLiveInterimTranscript('');
      setWsTranscriptSegments(prev => {
        // Find if this segment exists or append
        const exists = prev.some(s => s.text === msg.text);
        if (exists) return prev;
        return [...prev, {
          text: msg.text,
          confidence: msg.confidence,
          start: prev.length * 5.0, // mock increment
          end: (prev.length + 1) * 5.0
        }];
      });
    } else {
      setLiveInterimTranscript(msg.text);
    }
  };

  const handleVoiceCommand = (cmdResponse) => {
    setLastVoiceCommand(cmdResponse);
    
    // Process UI routing triggered via voice
    if (cmdResponse.action === 'show_questions') {
      setActiveTab('dashboard');
      // Scroll to Questions panel could be triggered via a custom event
      setTimeout(() => {
        const el = document.getElementById('questions-log');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 300);
    } else if (cmdResponse.action === 'translate_dashboard') {
      // Trigger translate on the active detail page
      const code = cmdResponse.payload?.language;
      if (code) {
        // Trigger a custom event to change target translation language
        window.dispatchEvent(new CustomEvent('voice-translate', { detail: code }));
      }
    } else if (cmdResponse.action === 'export_report') {
      const format = cmdResponse.payload?.format || 'pdf';
      window.open(`/report/${activeMeetingId}?format=${format}`, '_blank');
    }
  };

  // Switch translations triggered by voice commands
  useEffect(() => {
    const handleVoiceTranslate = (e) => {
      const langCode = e.detail;
      // We trigger a reload on detail view using dynamic bindings
    };
    window.addEventListener('voice-translate', handleVoiceTranslate);
    return () => window.removeEventListener('voice-translate', handleVoiceTranslate);
  }, []);

  if (!user) {
    return <Login onLoginSuccess={(u) => setUser(u)} />;
  }

  const isAdmin = user.role === 'admin';

  return (
    <div className="flex h-screen bg-[#080b11] overflow-hidden text-slate-100 font-sans">
      
      {/* Sidebar navigation */}
      <aside className="w-80 flex-shrink-0 flex flex-col h-full bg-[#07090e] border-r border-white/5">
        
        {/* Branding header */}
        <div className="p-5 border-b border-white/5 flex items-center gap-3 bg-white/[0.002]">
          <div className="bg-primary-600/10 p-2 rounded-xl text-primary-400 border border-primary-500/10">
            <Sparkles size={18} className="animate-pulse" />
          </div>
          <div>
            <h1 className="font-extrabold text-sm tracking-wide text-slate-100 uppercase">AI Meeting Assistant</h1>
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">MCA Project System</span>
          </div>
        </div>

        {/* Tab Buttons switcher */}
        <div className="p-4 grid grid-cols-2 gap-2 border-b border-white/5 bg-slate-950/20">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-bold transition-all duration-300 outline-none ${
              activeTab === 'dashboard'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-950/10'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.01]'
            }`}
          >
            <LayoutDashboard size={13} />
            <span>Dashboard</span>
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-bold transition-all duration-300 outline-none ${
              activeTab === 'analytics'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-950/10'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.01]'
            }`}
          >
            <Activity size={13} />
            <span>Workspace</span>
          </button>
        </div>

        {/* Upload Form Box */}
        <div className="p-4 border-b border-white/5 bg-[#090c14]/40 flex flex-col gap-3">
          {isAdmin ? (
            <form onSubmit={handleUploadSubmit} className="flex flex-col gap-3">
              <label 
                htmlFor="audio-upload"
                className={`border border-dashed border-white/10 hover:border-primary-500/50 rounded-xl p-3.5 flex flex-col items-center justify-center gap-2 cursor-pointer transition duration-300 ${
                  file ? 'bg-primary-500/[0.02] border-primary-500/30' : 'bg-transparent'
                }`}
              >
                <UploadCloud size={20} className={file ? 'text-primary-400' : 'text-slate-400'} />
                <div className="text-center">
                  <div className="text-xs font-semibold text-slate-200 truncate max-w-[200px]">
                    {file ? file.name : "Upload Meeting Audio"}
                  </div>
                  <div className="text-[10px] text-slate-500 font-medium mt-0.5">WAV, MP3, M4A, FLAC (Max 500MB)</div>
                </div>
                <input
                  id="audio-upload"
                  type="file"
                  accept=".wav,.mp3,.m4a,.flac,.ogg,.webm"
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={uploading}
                />
              </label>

              {file && (
                <div className="flex flex-col gap-2 animate-fadeIn">
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Meeting Title (optional)"
                    className="w-full bg-slate-900 border border-white/5 focus:border-primary-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 outline-none transition duration-200"
                  />
                  <button
                    type="submit"
                    disabled={uploading}
                    className="w-full py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-primary-800 text-xs font-bold rounded-lg text-white transition duration-200"
                  >
                    {uploading ? 'Processing...' : 'Analyze Audio File'}
                  </button>
                </div>
              )}
            </form>
          ) : (
            <div className="border border-dashed border-white/5 rounded-xl p-4 flex flex-col items-center justify-center gap-2 text-center text-slate-500 select-none bg-slate-950/10">
              <ShieldAlert size={20} className="text-slate-600" />
              <div className="text-xs font-semibold text-slate-400">Upload Restricted</div>
              <div className="text-[10px] text-slate-600 leading-relaxed">Administrator permissions are required to upload new meeting files.</div>
            </div>
          )}

          {/* Upload Status Banner */}
          {uploadStatus.message && (
            <div className={`p-2.5 rounded-lg border text-[11px] font-medium flex items-start gap-2 ${
              uploadStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
              uploadStatus.type === 'error' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' :
              uploadStatus.type === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
              'bg-slate-900 border-white/5 text-slate-400'
            }`}>
              <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
              <span>{uploadStatus.message}</span>
            </div>
          )}
        </div>

        {/* Live Audio recording toggle panel */}
        <div className="p-4 border-b border-white/5 bg-[#090c14]/20">
          {isAdmin ? (
            <LiveDetectionToggle
              onSessionStart={handleSessionStart}
              onSessionStop={handleSessionStop}
              onTranscriptUpdate={handleTranscriptUpdate}
              onVoiceCommand={handleVoiceCommand}
              activeMeetingId={activeMeetingId}
            />
          ) : (
            <div className="border border-dashed border-white/5 rounded-xl p-4.5 flex flex-col items-center justify-center gap-2 text-center text-slate-500 select-none bg-slate-950/10">
              <ShieldAlert size={20} className="text-slate-600" />
              <div className="text-xs font-semibold text-slate-400">Live Recording Restricted</div>
              <div className="text-[10px] text-slate-600 leading-relaxed">Administrator permissions are required to start dictation streams.</div>
            </div>
          )}
        </div>

        {/* Search & History List */}
        <div className="flex-1 overflow-hidden">
          <MeetingHistory
            activeMeetingId={activeMeetingId}
            onSelectMeeting={(id) => {
              setActiveMeetingId(id);
              setActiveTab('dashboard');
            }}
            refreshTrigger={refreshTrigger}
            onRefresh={triggerRefresh}
          />
        </div>

        {/* User Card Profile & Logout */}
        <div className="p-4 border-t border-white/5 bg-slate-950/20 flex items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2.5">
            <div className={`p-2 rounded-lg border font-bold uppercase tracking-wider flex items-center justify-center ${
              isAdmin ? 'bg-primary-600/10 border-primary-500/10 text-primary-400' : 'bg-slate-900 border-white/5 text-slate-300'
            }`}>
              {user.username.slice(0, 2)}
            </div>
            <div>
              <div className="font-semibold text-slate-200 capitalize">{user.username}</div>
              <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-0.25">{user.role} Account</div>
            </div>
          </div>
          <button
            onClick={() => { setUser(null); setActiveMeetingId(null); }}
            title="Log Out"
            className="p-2 bg-slate-900 hover:bg-slate-800 border border-white/5 hover:border-white/10 rounded-lg text-slate-400 hover:text-slate-200 transition duration-200 outline-none"
          >
            <LogOut size={13} />
          </button>
        </div>

      </aside>

      {/* Main Panel Content Area */}
      <main className="flex-1 h-full overflow-hidden flex flex-col bg-[#0b0f19]">
        {activeTab === 'analytics' ? (
          <AnalyticsOverview />
        ) : activeMeetingId ? (
          <MeetingDetail
            meetingId={activeMeetingId}
            activeSessionId={activeSessionId}
            wsTranscriptSegments={wsTranscriptSegments}
            liveInterimTranscript={liveInterimTranscript}
            userRole={user.role}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-4 py-20 select-none">
            <div className="bg-slate-900/60 border border-white/5 p-5 rounded-2xl text-slate-400 shadow-xl max-w-sm text-center flex flex-col items-center gap-3">
              <FileAudio size={40} className="text-slate-600 animate-pulse" />
              <h3 className="font-bold text-slate-300">No Selected Session</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Select a meeting from the sidebar logs, upload a pre-recorded audio file, or start a live recording session to view metrics dashboard.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Overlaid Voice Command Status Toast */}
      <VoiceCommandBar lastCommand={lastVoiceCommand} />

    </div>
  );
}
