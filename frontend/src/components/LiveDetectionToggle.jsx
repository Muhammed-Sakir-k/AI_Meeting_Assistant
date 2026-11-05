import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Square, Play } from 'lucide-react';

export default function LiveDetectionToggle({ onSessionStart, onSessionStop, onTranscriptUpdate, onVoiceCommand, activeMeetingId }) {
  const [isRecording, setIsRecording] = useState(false);
  const [session, setSession] = useState(null); // { sessionId, meetingId }
  const [speechStatus, setSpeechStatus] = useState("Idle");
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize Web Speech API for voice commands
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = false;
      rec.lang = 'en-US';
      
      rec.onresult = async (event) => {
        const lastIndex = event.results.length - 1;
        const text = event.results[lastIndex][0].transcript.trim();
        console.log("Voice Command Detected:", text);
        setSpeechStatus(`Command: "${text}"`);
        
        // Post voice command to backend
        try {
          const res = await fetch('/voice-command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: text, meeting_id: activeMeetingId })
          });
          if (res.ok) {
            const data = await res.json();
            onVoiceCommand(data);
            
            // Handle local actions based on command response
            if (data.action === "start_recording" && !isRecording) {
              startLiveSession();
            } else if (data.action === "stop_recording" && isRecording) {
              stopLiveSession();
            }
          }
        } catch (err) {
          console.error("Failed to route voice command:", err);
        }
      };

      rec.onerror = (e) => {
        console.warn("Speech recognition error:", e.error);
        if (e.error === 'not-allowed') {
          setSpeechStatus("Speech permission denied");
        }
      };

      rec.onend = () => {
        // Automatically restart speech recognition for always-on command listening when recording is active
        if (isRecording && recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            console.error("Error restarting SpeechRecognition:", e);
          }
        }
      };

      recognitionRef.current = rec;
    } else {
      console.warn("Speech Recognition API not supported in this browser.");
      setSpeechStatus("Voice commands unsupported");
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      }
    };
  }, [isRecording, activeMeetingId]);

  const startLiveSession = async () => {
    try {
      // 1. Get mic permissions and stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      // 2. Call backend to start live session
      const formData = new FormData();
      formData.append('title', `Live Sync Session - ${new Date().toLocaleTimeString()}`);
      
      const res = await fetch('/live/start', {
        method: 'POST',
        body: formData
      });
      
      if (!res.ok) throw new Error("Failed to start session on backend");
      const data = await res.json();
      
      const sessionId = data.session_id;
      const meetingId = data.meeting_id;
      setSession({ sessionId, meetingId });
      onSessionStart(meetingId, sessionId);

      // 3. Establish WebSocket connection
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${protocol}://${window.location.host}/ws/live/${sessionId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket stream connected");
        setIsRecording(true);
        setSpeechStatus("Listening...");
        
        // Start always-on voice command listening
        if (recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            console.error("Speech recognition start failed:", e);
          }
        }
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "transcript") {
          onTranscriptUpdate(msg);
        } else if (msg.type === "info") {
          console.info("WS Info:", msg.message);
        } else if (msg.type === "error") {
          console.error("WS Error:", msg.message);
        }
      };

      ws.onclose = () => {
        console.log("WebSocket stream closed");
        setIsRecording(false);
      };

      ws.onerror = (err) => {
        console.error("WS Error:", err);
      };

      // 4. Capture Mic Audio and convert to 16kHz PCM mono
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioContext;
      
      const source = audioContext.createMediaStreamSource(stream);
      
      // Create script processor to read raw PCM audio samples
      const bufferSize = 2048;
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (ws.readyState !== WebSocket.OPEN) return;
        
        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32 array to Int16 PCM array
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          // Clamp values between -1.0 and 1.0
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Send binary buffer to WebSocket
        ws.send(pcmData.buffer);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

    } catch (err) {
      console.error("Live detection permission or launch error:", err);
      alert("Microphone permission denied or connection issue: " + err.message);
      setIsRecording(false);
      setSpeechStatus("Permission denied");
    }
  };

  const stopLiveSession = async () => {
    if (!session) return;
    setIsRecording(false);
    setSpeechStatus("Finalizing...");

    // 1. Stop audio processing nodes
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    // 2. Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // 3. Stop recognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }

    // 4. Hit backend to finalize session
    try {
      const res = await fetch(`/live/stop/${session.sessionId}`, {
        method: 'POST'
      });
      if (res.ok) {
        onSessionStop(session.meetingId);
      }
    } catch (err) {
      console.error("Error stopping live session:", err);
    } finally {
      setSession(null);
      setSpeechStatus("Idle");
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopLiveSession();
    } else {
      startLiveSession();
    }
  };

  return (
    <div className="flex flex-col gap-2 p-3 glass-card rounded-xl border border-white/5 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isRecording ? 'bg-green-500 pulse-active' : 'bg-slate-500'}`}></div>
          <span className="text-sm font-medium text-slate-200">
            {isRecording ? "Live Meeting Active" : "Live Detection"}
          </span>
        </div>
        <span className="text-xs text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
          {speechStatus}
        </span>
      </div>
      
      <button
        type="button"
        onClick={toggleRecording}
        className={`w-full py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 font-semibold text-sm transition-all duration-300 ${
          isRecording
            ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-950/20'
            : 'bg-primary-600 hover:bg-primary-500 text-white shadow-primary-950/20'
        } shadow-md`}
      >
        {isRecording ? (
          <>
            <MicOff size={16} />
            <span>Stop Live Session</span>
          </>
        ) : (
          <>
            <Mic size={16} />
            <span>Start Live Session</span>
          </>
        )}
      </button>
    </div>
  );
}
