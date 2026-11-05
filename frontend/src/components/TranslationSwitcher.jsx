import React, { useState, useEffect } from 'react';
import { Languages, Loader2 } from 'lucide-react';

export default function TranslationSwitcher({ activeLanguage, onLanguageChange }) {
  const [languages, setLanguages] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        const res = await fetch('/languages');
        if (res.ok) {
          const data = await res.json();
          setLanguages(data);
        }
      } catch (err) {
        console.error("Failed to load translation languages:", err);
      }
    };
    fetchLanguages();
  }, []);

  const handleLangSelect = async (e) => {
    const langCode = e.target.value;
    setLoading(true);
    try {
      await onLanguageChange(langCode);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2 bg-slate-900 border border-white/5 rounded-lg px-2.5 py-1.5 shadow-md">
      {loading ? (
        <Loader2 size={14} className="text-primary-400 animate-spin" />
      ) : (
        <Languages size={14} className="text-slate-400" />
      )}
      
      <select
        value={activeLanguage}
        onChange={handleLangSelect}
        disabled={loading}
        className="bg-transparent text-xs font-semibold text-slate-200 outline-none border-none cursor-pointer disabled:opacity-50"
      >
        <option value="original" className="bg-slate-950 text-slate-200">Original Transcript</option>
        {Object.entries(languages).map(([code, name]) => (
          <option key={code} value={code} className="bg-slate-950 text-slate-200">
            Translate: {name}
          </option>
        ))}
      </select>
    </div>
  );
}
