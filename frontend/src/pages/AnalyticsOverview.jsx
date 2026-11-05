import React, { useState, useEffect } from 'react';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { RefreshCw, Users, Clock, ClipboardList, Languages, Calendar, AlertCircle, Activity } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
  BarElement
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
  BarElement
);

export default function AnalyticsOverview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAggregateAnalytics();
  }, []);

  const fetchAggregateAnalytics = async () => {
    setLoading(true);
    try {
      const res = await fetch('/analytics/aggregate');
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error("Failed to fetch aggregate analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex-grow flex items-center justify-center text-slate-500 text-sm gap-2 h-full">
        <RefreshCw size={18} className="animate-spin" />
        <span>Compiling workspace analytics...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 text-center italic text-slate-500 flex flex-col items-center gap-2">
        <AlertCircle size={28} />
        <span>Failed to load workspace data.</span>
      </div>
    );
  }

  // Format Duration
  const formatDuration = (seconds) => {
    if (!seconds) return "0s";
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  // 1. Language Distribution Chart
  const langDist = data.language_distribution || {};
  const langChartData = {
    labels: Object.keys(langDist).map(l => l.toUpperCase()),
    datasets: [
      {
        data: Object.values(langDist),
        backgroundColor: ['rgba(139, 92, 246, 0.75)', 'rgba(59, 130, 246, 0.75)', 'rgba(16, 185, 129, 0.75)'],
        borderColor: ['#8b5cf6', '#3b82f6', '#10b981'],
        borderWidth: 1,
      }
    ]
  };

  // 2. Aggregate Sentiment Chart
  const sentDist = data.aggregate_sentiment || { positive: 0, neutral: 100, negative: 0 };
  const sentimentChartData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [sentDist.positive, sentDist.neutral, sentDist.negative],
        backgroundColor: ['rgba(34, 197, 94, 0.7)', 'rgba(100, 116, 139, 0.7)', 'rgba(244, 63, 94, 0.7)'],
        borderColor: ['#22c55e', '#64748b', '#f43f5e'],
        borderWidth: 1,
      }
    ]
  };

  // 3. Meeting Frequency Line Chart
  const freq = data.meeting_frequency || [];
  const freqChartData = {
    labels: freq.map(f => f.date),
    datasets: [
      {
        label: 'Meetings',
        data: freq.map(f => f.count),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.05)',
        tension: 0.35,
        fill: true,
        borderWidth: 2,
        pointBackgroundColor: '#3b82f6',
        pointRadius: 4,
      }
    ]
  };

  // 4. Most Active Members Bar Chart
  const activeParticipants = data.most_active_participants || {};
  const participantChartData = {
    labels: Object.keys(activeParticipants),
    datasets: [
      {
        label: 'Action Items Assigned',
        data: Object.values(activeParticipants),
        backgroundColor: 'rgba(16, 185, 129, 0.7)',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, ticks: { color: '#64748b', font: { size: 9.5 } } },
      y: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, ticks: { color: '#64748b', stepSize: 1, font: { size: 9.5 } } }
    }
  };

  return (
    <div className="flex-1 p-6 bg-[#0b0f19] overflow-y-auto h-full">
      {/* Page Header */}
      <header className="mb-6 flex items-center justify-between border-b border-white/5 pb-4.5">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Activity size={22} className="text-primary-500" />
            <span>Workspace Analytics</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Cross-meeting overview, team engagement metrics, and meeting frequency data.</p>
        </div>
        <button
          onClick={fetchAggregateAnalytics}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-900 border border-white/5 hover:border-white/10 rounded-lg text-slate-300 transition duration-200"
        >
          <RefreshCw size={12} />
          <span>Refresh</span>
        </button>
      </header>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {/* Total Meetings */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-primary-500/10 p-2.5 rounded-lg text-primary-400">
            <Calendar size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Meetings</div>
            <div className="text-lg font-bold text-slate-100">{data.total_meetings}</div>
          </div>
        </div>

        {/* Avg Duration */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-emerald-500/10 p-2.5 rounded-lg text-emerald-400">
            <Clock size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Avg Duration</div>
            <div className="text-lg font-bold text-slate-100">{formatDuration(data.average_duration_seconds)}</div>
          </div>
        </div>

        {/* Avg Tasks */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-amber-500/10 p-2.5 rounded-lg text-amber-400">
            <ClipboardList size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Avg Action Items</div>
            <div className="text-lg font-bold text-slate-100">{data.average_action_items} / mtg</div>
          </div>
        </div>

        {/* Total Languages */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-blue-500/10 p-2.5 rounded-lg text-blue-400">
            <Languages size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Languages Used</div>
            <div className="text-lg font-bold text-slate-100">{Object.keys(langDist).length}</div>
          </div>
        </div>
      </div>

      {/* Grid Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Frequency Timeline Chart */}
        <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col h-[280px]">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Calendar size={14} className="text-blue-400" />
            <span>Meeting Frequency Over Time</span>
          </h3>
          <div className="flex-1 min-h-[160px]">
            {freq.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">No timeline data available.</div>
            ) : (
              <Line data={freqChartData} options={chartOptions} />
            )}
          </div>
        </div>

        {/* Most Active Participants Chart */}
        <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col h-[280px]">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Users size={14} className="text-emerald-400" />
            <span>Most Active Participants</span>
          </h3>
          <div className="flex-1 min-h-[160px]">
            {Object.keys(activeParticipants).length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">No participant task records found.</div>
            ) : (
              <Bar data={participantChartData} options={chartOptions} />
            )}
          </div>
        </div>

        {/* Tone Distribution */}
        <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col h-[280px]">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Activity size={14} className="text-purple-400" />
            <span>Workspace Sentiment</span>
          </h3>
          <div className="flex-1 relative min-h-[160px]">
            <Doughnut
              data={sentimentChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 10 }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* Languages Pie */}
        <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col h-[280px]">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Languages size={14} className="text-primary-400" />
            <span>Language Distribution</span>
          </h3>
          <div className="flex-1 relative min-h-[160px]">
            {Object.keys(langDist).length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">No language data recorded.</div>
            ) : (
              <Doughnut
                data={langChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                      labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 10 }
                    }
                  }
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
