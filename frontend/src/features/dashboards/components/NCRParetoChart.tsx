import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bar } from 'react-chartjs-2';
import { BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
import { Chart as ChartJS } from 'chart.js';
import apiClient from '@/services/api.client';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

interface NCRData {
  defect_type: string;
  count: number;
  cumulative_percentage: number;
}

interface NCRParetoChartProps {
  plantId?: number;
  days?: number;
}

/**
 * NCR Pareto Chart
 *
 * Displays top defect types in descending order with cumulative percentage.
 * Helps identify the "vital few" defects causing most quality issues.
 *
 * 80/20 rule: 80% of defects come from 20% of defect types.
 */
export const NCRParetoChart: React.FC<NCRParetoChartProps> = ({ plantId, days = 30 }) => {
  const { data, isLoading, error } = useQuery<NCRData[]>({
    queryKey: ['ncr-pareto', plantId, days],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (plantId) params.append('plant_id', String(plantId));
      params.append('days', String(days));

      const response = await apiClient.get<NCRData[]>(
        `/api/v1/analytics/ncr-pareto?${params.toString()}`
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
        Failed to load NCR data: {error.message}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        <p>No NCR data available for the selected period</p>
        <p className="text-sm mt-1">This is great - no quality issues reported!</p>
      </div>
    );
  }

  const totalNCRs = data.reduce((sum, d) => sum + d.count, 0);

  // Prepare chart data
  const chartData = {
    labels: data.map(d => d.defect_type),
    datasets: [
      {
        type: 'bar' as const,
        label: 'NCR Count',
        data: data.map(d => d.count),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        type: 'line' as const,
        label: 'Cumulative %',
        data: data.map(d => d.cumulative_percentage),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: 'rgb(239, 68, 68)',
        yAxisID: 'y1',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'NCR Pareto Analysis - Top Defect Types',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.dataset.yAxisID === 'y1') {
              label += context.parsed.y.toFixed(1) + '%';
            } else {
              label += context.parsed.y + ' NCRs';
            }
            return label;
          },
        },
      },
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        beginAtZero: true,
        title: {
          display: true,
          text: 'NCR Count',
        },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        beginAtZero: true,
        max: 100,
        grid: {
          drawOnChartArea: false,
        },
        title: {
          display: true,
          text: 'Cumulative %',
        },
        ticks: {
          callback: function (value: any) {
            return value + '%';
          },
        },
      },
      x: {
        title: {
          display: true,
          text: 'Defect Type',
        },
      },
    },
  };

  // Find the 80% threshold index
  const threshold80Index = data.findIndex(d => d.cumulative_percentage >= 80);
  const vital20Percent = threshold80Index >= 0 ? threshold80Index + 1 : data.length;

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total NCRs</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{totalNCRs}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Defect Types</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{data.length}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Vital 20% (80/20 Rule)</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {vital20Percent} types
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6" style={{ height: '450px' }}>
        <Bar data={chartData} options={chartOptions} />
      </div>

      {/* Top Defects Table */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 5 Defect Types</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Defect Type
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Count
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  % of Total
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Cumulative %
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.slice(0, 5).map((item, index) => (
                <tr key={item.defect_type} className={index < vital20Percent ? 'bg-blue-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{index + 1}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.defect_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {item.count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                    {((item.count / totalNCRs) * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                    {item.cumulative_percentage.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pareto Insight */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="text-sm font-medium text-blue-800">📊 Pareto Insight</div>
        <div className="text-xs text-blue-700 mt-1">
          {vital20Percent} defect types account for 80% of all NCRs. Focus quality improvement efforts on these vital few for maximum impact.
        </div>
      </div>
    </div>
  );
};

export default NCRParetoChart;
