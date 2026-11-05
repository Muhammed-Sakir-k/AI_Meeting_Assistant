import React from 'react';
import { Line } from 'react-chartjs-2';
import { Heart, Activity } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function SentimentTimeline({ sentimentData }) {
  const formatTime = (seconds) => {
    if (seconds == null || isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Process data for Chart.js
  const sortedData = [...sentimentData].sort((a, b) => a.segment_index - b.segment_index);
  
  const labels = sortedData.map(s => formatTime(s.start_time));
  const dataPoints = sortedData.map(s => {
    const lbl = (s.label || 'neutral').toLowerCase();
    const score = s.score || 0.5;
    if (lbl === 'positive') return score;
    if (lbl === 'negative') return -score;
    return 0; // neutral
  });

  const chartData = {
    labels: labels.length > 0 ? labels : ['0:00'],
    datasets: [
      {
        label: 'Sentiment Score',
        data: dataPoints.length > 0 ? dataPoints : [0],
        borderColor: '#8b5cf6', // primary purple
        backgroundColor: 'rgba(139, 92, 246, 0.05)',
        tension: 0.35,
        fill: true,
        pointBackgroundColor: (context) => {
          const index = context.dataIndex;
          const val = context.dataset.data[index];
          if (val > 0.1) return '#22c55e'; // green for positive
          if (val < -0.1) return '#f43f5e'; // red for negative
          return '#64748b'; // slate for neutral
        },
        pointRadius: 4.5,
        pointHoverRadius: 6,
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const val = context.parsed.y;
            if (val > 0.1) return `Positive: ${Math.round(val * 100)}%`;
            if (val < -0.1) return `Negative: ${Math.round(Math.abs(val) * 100)}%`;
            return 'Neutral';
          }
        },
        backgroundColor: '#0f172a',
        titleColor: '#94a3b8',
        bodyColor: '#f8fafc',
        borderColor: 'rgba(255, 255, 255, 0.08)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.03)',
        },
        ticks: {
          color: '#64748b',
          font: { size: 10 },
          maxRotation: 45,
          minRotation: 0,
        }
      },
      y: {
        min: -1.0,
        max: 1.0,
        grid: {
          color: 'rgba(255, 255, 255, 0.04)',
        },
        ticks: {
          color: '#64748b',
          font: { size: 10 },
          callback: (value) => {
            if (value === 1.0) return 'POS';
            if (value === 0.0) return 'NEU';
            if (value === -1.0) return 'NEG';
            return '';
          }
        }
      }
    }
  };

  return (
    <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl p-5 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="bg-purple-500/10 p-2 rounded-lg text-purple-400">
            <Activity size={18} />
          </div>
          <h3 className="font-semibold text-slate-100">Sentiment Timeline</h3>
        </div>
        <div className="flex gap-4 text-[10px] font-semibold text-slate-400">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span> POSITIVE</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-500 inline-block"></span> NEUTRAL</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500 inline-block"></span> NEGATIVE</span>
        </div>
      </div>

      <div className="flex-1 min-h-[200px] h-[240px]">
        {sentimentData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm italic">
            No sentiment data recorded yet.
          </div>
        ) : (
          <Line data={chartData} options={chartOptions} />
        )}
      </div>
    </div>
  );
}
