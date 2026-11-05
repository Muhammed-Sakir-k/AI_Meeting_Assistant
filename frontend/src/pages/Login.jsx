import React, { useState } from 'react';
import { Sparkles, Shield, User, Lock, ArrowRight, AlertCircle } from 'lucide-react';

export default function Login({ onLoginSuccess }) {
  const [isAdmin, setIsAdmin] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (res.ok) {
        const data = await res.json();
        // Restrict standard users from logging into admin portal portal tab
        if (isAdmin && data.role !== 'admin') {
          setError('Access denied. Administrator credentials required.');
        } else {
          onLoginSuccess(data);
        }
      } else {
        const err = await res.json();
        setError(err.detail || 'Invalid username or password.');
      }
    } catch (err) {
      setError('Connection to backend auth server failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (role) => {
    if (role === 'admin') {
      setIsAdmin(true);
      setUsername('admin');
      setPassword('admin123');
    } else {
      setIsAdmin(false);
      setUsername('user');
      setPassword('user123');
    }
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080b11] p-4 font-sans select-none relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>

      <div className="w-full max-w-md glass-panel rounded-2xl border border-white/5 shadow-2xl p-8 relative z-10 bg-slate-950/20 backdrop-blur-xl">
        
        {/* Branding header */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-primary-600/10 p-3.5 rounded-2xl text-primary-400 border border-primary-500/15 mb-3.5 shadow-inner">
            <Sparkles size={28} className="animate-pulse" />
          </div>
          <h1 className="text-xl font-black text-slate-100 uppercase tracking-wide">AI Meeting Assistant</h1>
          <span className="text-xs text-slate-500 font-semibold mt-1">MCA Project System</span>
        </div>

        {/* Tab switchers */}
        <div className="grid grid-cols-2 gap-2 bg-slate-950/40 p-1.5 rounded-xl border border-white/5 mb-6 text-xs font-bold">
          <button
            type="button"
            onClick={() => { setIsAdmin(false); setError(''); }}
            className={`py-2 px-3 rounded-lg flex items-center justify-center gap-1.5 transition duration-200 outline-none ${
              !isAdmin ? 'bg-primary-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <User size={13} />
            <span>User Account</span>
          </button>
          <button
            type="button"
            onClick={() => { setIsAdmin(true); setError(''); }}
            className={`py-2 px-3 rounded-lg flex items-center justify-center gap-1.5 transition duration-200 outline-none ${
              isAdmin ? 'bg-primary-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Shield size={13} />
            <span>Admin Portal</span>
          </button>
        </div>

        {/* Login form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 pl-1">Username</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <User size={14} />
              </div>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={isAdmin ? "Enter admin username" : "Enter user username"}
                className="w-full bg-slate-900/60 border border-white/5 focus:border-primary-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition duration-200"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 pl-1">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <Lock size={14} />
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900/60 border border-white/5 focus:border-primary-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition duration-200"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-2 text-xs text-rose-400 animate-fadeIn">
              <AlertCircle size={15} className="flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-primary-600 hover:bg-primary-500 active:bg-primary-700 text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition duration-200 shadow-lg shadow-primary-950/20"
          >
            <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
            {!loading && <ArrowRight size={15} />}
          </button>
        </form>

        {/* Quick Fill Helpers */}
        <div className="mt-8 pt-6 border-t border-white/5 text-center">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-3">Quick Fill Credentials</span>
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => handleQuickFill('user')}
              className="text-[11px] font-semibold bg-slate-900 border border-white/5 hover:border-white/10 px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition"
            >
              Fill User demo
            </button>
            <button
              onClick={() => handleQuickFill('admin')}
              className="text-[11px] font-semibold bg-slate-900 border border-white/5 hover:border-white/10 px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition"
            >
              Fill Admin demo
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
