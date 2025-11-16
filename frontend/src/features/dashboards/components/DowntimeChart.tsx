import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import apiClient from '@/services/api.client';

ChartJS.register(ArcElement, Tooltip, Legend);

interface DowntimeData {
  reason: string;
  duration_minutes: number;
  occurrence_count: number;
  percentage: number;
}

interface DowntimeChartProps {
  plantId?: number;
  days?: number;
}

/**
 * Downtime Analysis Chart
 *
 * Displays machine downtime reasons with duration and frequency.
 * Helps identify the biggest causes of production losses.
 */
export const DowntimeChart: React.FC<DowntimeChartProps> = ({ plantId, days = 30 }) => {
  const { data, isLoading, error } = useQuery<DowntimeData[]>({
    queryKey: ['downtime-data', plantId, days],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (plantId) params.append('plant_id', String(plantId));
      params.append('days', String(days));

      const response = await apiClient.get<DowntimeData[]>(
        `/api/v1/analytics/downtime?${params.toString()}`
      );
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Failed to load downtime data: {error.message}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        <p>No downtime data available for the selected period</p>
        <p className="text-sm mt-1">Excellent - minimal downtime!</p>
      </div>
    );
  }

  const totalDowntime = data.reduce((sum, d) => sum + d.duration_minutes, 0);
  const totalOccurrences = data.reduce((sum, d) => sum + d.occurrence_count, 0);

  // Prepare chart data
  const chartData = {
    labels: data.map(d => d.reason),
    datasets: [
      {
        data: data.map(d => d.duration_minutes),
        backgroundColor: [
          'rgba(239, 68, 68, 0.7)',
          'rgba(251, 146, 60, 0.7)',
          'rgba(251, 191, 36, 0.7)',
          'rgba(34, 197, 94, 0.7)',
          'rgba(59, 130, 246, 0.7)',
          'rgba(147, 51, 234, 0.7)',
          'rgba(236, 72, 153, 0.7)',
        ],
        borderColor: [
          'rgb(239, 68, 68)',
          'rgb(251, 146, 60)',
          'rgb(251, 191, 36)',
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)',
          'rgb(147, 51, 234)',
          'rgb(236, 72, 153)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
      title: {
        display: true,
        text: 'Downtime by Reason',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const label = context.label || '';
            const value = context.parsed;
            const hours = (value / 60).toFixed(1);
            const percentage = context.dataset.data
              ? ((value / context.dataset.data.reduce((a: number, b: number) => a + b, 0)) * 100).toFixed(1)
              : '0';
            return `${label}: ${hours} hrs (${percentage}%)`;
          },
        },
      },
    },
  };

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Downtime</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {(totalDowntime / 60).toFixed(1)} hrs
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Downtime Events</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{totalOccurrences}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Avg Event Duration</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {totalOccurrences > 0 ? (totalDowntime / totalOccurrences).toFixed(0) : 0} min
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6" style={{ height: '400px' }}>
        <Pie data={chartData} options={chartOptions} />
      </div>

      {/* Downtime Breakdown Table */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Downtime Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Reason
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Duration (hrs)
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Occurrences
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Avg Duration
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  % of Total
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item, index) => (
                <tr key={item.reason} className={index === 0 ? 'bg-red-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {(item.duration_minutes / 60).toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                    {item.occurrence_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                    {(item.duration_minutes / item.occurrence_count).toFixed(0)} min
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                    {item.percentage.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Issue Alert */}
      {data.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm font-medium text-red-800">🔴 Top Downtime Issue</div>
          <div className="text-xs text-red-700 mt-1">
            <strong>{data[0].reason}</strong> accounts for {data[0].percentage.toFixed(1)}% of all downtime
            ({(data[0].duration_minutes / 60).toFixed(1)} hours). Focus improvement efforts here for maximum impact.
          </div>
        </div>
      )}
    </div>
  );
};

export default DowntimeChart;
