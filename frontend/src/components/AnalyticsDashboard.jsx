import React from 'react';
import { Doughnut, Bar } from 'react-chartjs-2';
import { BarChart3, PieChart, Sparkles, Clock, HelpCircle, FileText } from 'lucide-react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement
} from 'chart.js';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement
);

export default function AnalyticsDashboard({ analytics }) {
  if (!analytics || Object.keys(analytics).length === 0) {
    return (
      <div className="card glass-panel rounded-2xl border border-white/5 shadow-2xl p-6 text-center italic text-slate-500">
        No analytics compiled for this session yet. Complete analysis to view metrics.
      </div>
    );
  }

  // Format Duration
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  // 1. Sentiment Distribution Doughnut
  const sentDist = analytics.sentiment_distribution || { positive: 0, neutral: 100, negative: 0 };
  const sentimentChartData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [sentDist.positive, sentDist.neutral, sentDist.negative],
        backgroundColor: [
          'rgba(34, 197, 94, 0.75)',  // green
          'rgba(148, 163, 184, 0.75)', // slate
          'rgba(244, 63, 94, 0.75)'    // rose
        ],
        borderColor: [
          '#22c55e',
          '#94a3b8',
          '#f43f5e'
        ],
        borderWidth: 1,
      },
    ],
  };

  // 2. Action Priority Chart
  const priorities = analytics.priority_distribution || { high: 0, medium: 0, low: 0 };
  const priorityChartData = {
    labels: ['High', 'Medium', 'Low'],
    datasets: [
      {
        label: 'Action Items',
        data: [priorities.high, priorities.medium, priorities.low],
        backgroundColor: [
          'rgba(244, 63, 94, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(16, 185, 129, 0.7)'
        ],
        borderColor: [
          '#f43f5e',
          '#f59e0b',
          '#10b981'
        ],
        borderWidth: 1,
      },
    ],
  };

  // 3. Top Keywords Bar Chart
  const keywords = analytics.top_keywords || {};
  const keywordLabels = Object.keys(keywords);
  const keywordData = Object.values(keywords);

  const keywordChartData = {
    labels: keywordLabels.length > 0 ? keywordLabels : ['None'],
    datasets: [
      {
        label: 'Frequency',
        data: keywordData.length > 0 ? keywordData : [0],
        backgroundColor: 'rgba(139, 92, 246, 0.6)',
        borderColor: '#8b5cf6',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 9.5 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', stepSize: 1, font: { size: 9.5 } }
      }
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric: Duration */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-primary-500/10 p-2.5 rounded-lg text-primary-400">
            <Clock size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Duration</div>
            <div className="text-base font-bold text-slate-100">{formatDuration(analytics.duration_seconds)}</div>
          </div>
        </div>

        {/* Metric: Word Count */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-emerald-500/10 p-2.5 rounded-lg text-emerald-400">
            <FileText size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Words</div>
            <div className="text-base font-bold text-slate-100">{analytics.word_count}</div>
          </div>
        </div>

        {/* Metric: Action items completed */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-purple-500/10 p-2.5 rounded-lg text-purple-400">
            <BarChart3 size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Action Items</div>
            <div className="text-base font-bold text-slate-100">
              {analytics.action_items_completed}/{analytics.action_items_total} Done
            </div>
          </div>
        </div>

        {/* Metric: Questions answered */}
        <div className="glass-panel p-4.5 rounded-xl border border-white/5 shadow-md flex items-center gap-4">
          <div className="bg-blue-500/10 p-2.5 rounded-lg text-blue-400">
            <HelpCircle size={20} />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Questions</div>
            <div className="text-base font-bold text-slate-100">
              {analytics.questions_answered}/{analytics.questions_total} Solved
            </div>
          </div>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Doughnut Sentiment */}
        <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col h-[280px]">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2 mb-4">
            <PieChart size={14} className="text-primary-400" />
            <span>Tone Distribution</span>
          </h4>
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

        {/* Bar Priority */}
        <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col h-[280px]">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2 mb-4">
            <BarChart3 size={14} className="text-primary-400" />
            <span>Task Priorities</span>
          </h4>
          <div className="flex-1 min-h-[160px]">
            <Bar data={priorityChartData} options={chartOptions} />
          </div>
        </div>

        {/* Bar Topics/Keywords */}
        <div className="glass-panel p-5 rounded-2xl border border-white/5 flex flex-col h-[280px]">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2 mb-4">
            <Sparkles size={14} className="text-primary-400" />
            <span>Frequent Keywords</span>
          </h4>
          <div className="flex-1 min-h-[160px]">
            <Bar data={keywordChartData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
