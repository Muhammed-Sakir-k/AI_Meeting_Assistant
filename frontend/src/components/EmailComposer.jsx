import React, { useState, useEffect } from 'react';
import { Mail, Send, Copy, RefreshCw, Check } from 'lucide-react';

export default function EmailComposer({ meetingId, userRole }) {
  const [draftType, setDraftType] = useState('mom'); // mom, action_assignment, followup
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [sending, setSending] = useState(false);
  const [sentMessage, setSentMessage] = useState('');
  
  const isAdmin = userRole === 'admin';

  // Fetch email draft when type changes
  useEffect(() => {
    fetchDraft();
  }, [draftType, meetingId]);

  const fetchDraft = async () => {
    setLoading(true);
    setSentMessage('');
    try {
      const res = await fetch(`/email/draft/${meetingId}?type=${draftType}`);
      if (res.ok) {
        const data = await res.json();
        setSubject(data.subject || '');
        setBody(data.body || '');
        
        // Join recipient list
        const rcps = data.recipients || [];
        setRecipient(rcps.join(', '));
      }
    } catch (err) {
      console.error("Error fetching email draft:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    const emailText = `To: ${recipient}\nSubject: ${subject}\n\n${body}`;
    try {
      await navigator.clipboard.writeText(emailText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Failed to copy email:", err);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!recipient || !subject || !body) {
      alert("Please fill in recipient, subject, and email body.");
      return;
    }

    setSending(true);
    setSentMessage('');
    try {
      const res = await fetch(`/email/send/${meetingId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient,
          subject,
          body,
          email_type: draftType
        })
      });
      if (res.ok) {
        setSentMessage("✓ Email dispatched successfully!");
      } else {
        const err = await res.json();
        setSentMessage(`✗ Sending failed: ${err.detail || 'check connection configuration'}`);
      }
    } catch (err) {
      setSentMessage("✗ Network delivery error.");
      console.error(err);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl p-5 flex flex-col h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 border-b border-white/5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="bg-emerald-500/10 p-2 rounded-lg text-emerald-400">
            <Mail size={18} />
          </div>
          <h3 className="font-semibold text-slate-100">AI Email Composer</h3>
        </div>

        {/* Draft Type Selector */}
        <div className="flex items-center bg-slate-900/60 p-0.5 rounded-lg border border-white/5">
          {[
            { id: 'mom', name: 'MOM' },
            { id: 'action_assignment', name: 'Tasks Assign' },
            { id: 'followup', name: 'Follow-up' }
          ].map(opt => (
            <button
              key={opt.id}
              onClick={() => setDraftType(opt.id)}
              className={`px-2.5 py-1 text-[10.5px] font-semibold rounded-md transition duration-200 outline-none ${
                draftType === opt.id
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {opt.name}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center py-12 text-slate-500 text-sm gap-2">
          <RefreshCw size={16} className="animate-spin" />
          <span>Composing draft...</span>
        </div>
      ) : (
        <form onSubmit={handleSend} className="flex-1 flex flex-col gap-3.5">
          {!isAdmin && (
            <div className="text-[10px] text-amber-400 font-semibold bg-amber-500/5 p-2 rounded border border-amber-500/10 mb-1">
              ⚠ Read-Only Mode: Administrator privileges are required to edit drafts or dispatch emails.
            </div>
          )}
          
          {/* Recipient */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Recipients (comma separated)</label>
            <input
              type="text"
              disabled={!isAdmin}
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder="e.g. manager@corp.com, dev@corp.com"
              className="bg-slate-950/60 border border-white/5 focus:border-primary-500 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {/* Subject */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Subject Line</label>
            <input
              type="text"
              disabled={!isAdmin}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Email subject"
              className="bg-slate-950/60 border border-white/5 focus:border-primary-500 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {/* Body */}
          <div className="flex-1 flex flex-col gap-1 min-h-[140px]">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Email Body</label>
            <textarea
              disabled={!isAdmin}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Draft body content..."
              className="flex-1 bg-slate-950/60 border border-white/5 focus:border-primary-500 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none transition duration-200 resize-none font-normal leading-relaxed h-[180px] overflow-y-auto disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between border-t border-white/5 pt-3">
            <span className={`text-xs font-semibold ${sentMessage.startsWith('✓') ? 'text-emerald-400' : 'text-rose-400'}`}>
              {sentMessage}
            </span>
            
            <div className="flex items-center gap-2">
              {/* Copy Button */}
              <button
                type="button"
                onClick={handleCopy}
                className="px-3 py-1.5 text-xs font-semibold bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded border border-white/5 flex items-center gap-1.5 transition duration-200"
              >
                {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              {/* Send Button */}
              <button
                type="submit"
                disabled={sending || !isAdmin}
                className="px-3.5 py-1.5 text-xs font-bold bg-primary-600 hover:bg-primary-500 disabled:bg-primary-800 text-white rounded flex items-center gap-1.5 transition duration-200 shadow-md shadow-primary-950/10 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? <RefreshCw size={13} className="animate-spin" /> : <Send size={13} />}
                <span>{sending ? 'Sending...' : 'Send Draft'}</span>
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
