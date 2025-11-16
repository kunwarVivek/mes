import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Line } from 'react-chartjs-2';
import { format } from 'date-fns';
import apiClient from '@/services/api.client';

interface FPYData {
  date: string;
  total_pieces: number;
  good_pieces: number;
  defect_pieces: number;
  fpy_percentage: number;
}

interface FPYChartProps {
  plantId?: number;
  days?: number;
}

/**
 * First Pass Yield (FPY) Chart
 *
 * Displays trend of first-time-right production.
 * FPY = (Good Pieces / Total Pieces) × 100
 *
 * Key quality metric indicating manufacturing efficiency.
 */
export const FPYChart: React.FC<FPYChartProps> = ({ plantId, days = 30 }) => {
  const { data, isLoading, error } = useQuery<FPYData[]>({
    queryKey: ['fpy-data', plantId, days],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (plantId) params.append('plant_id', String(plantId));
      params.append('days', String(days));

      const response = await apiClient.get<FPYData[]>(
        `/api/v1/analytics/fpy?${params.toString()}`
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
        Failed to load FPY data: {error.message}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        <p>No FPY data available for the selected period</p>
      </div>
    );
  }

  // Calculate summary metrics
  const totalPieces = data.reduce((sum, d) => sum + d.total_pieces, 0);
  const totalGood = data.reduce((sum, d) => sum + d.good_pieces, 0);
  const totalDefects = data.reduce((sum, d) => sum + d.defect_pieces, 0);
  const avgFPY = totalPieces > 0 ? (totalGood / totalPieces) * 100 : 0;

  // Prepare chart data
  const chartData = {
    labels: data.map(d => format(new Date(d.date), 'MMM dd')),
    datasets: [
      {
        label: 'FPY %',
        data: data.map(d => d.fpy_percentage),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Target (98%)',
        data: Array(data.length).fill(98),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        pointRadius: 0,
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
        text: 'First Pass Yield Trend',
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
            label += context.parsed.y.toFixed(1) + '%';
            return label;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function (value: any) {
            return value + '%';
          },
        },
        title: {
          display: true,
          text: 'First Pass Yield %',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Date',
        },
      },
    },
  };

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Average FPY</div>
          <div className={`text-2xl font-bold mt-1 ${avgFPY >= 98 ? 'text-green-600' : avgFPY >= 90 ? 'text-yellow-600' : 'text-red-600'}`}>
            {avgFPY.toFixed(1)}%
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Pieces</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{totalPieces.toLocaleString()}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Good Pieces</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{totalGood.toLocaleString()}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Defects</div>
          <div className="text-2xl font-bold text-red-600 mt-1">{totalDefects.toLocaleString()}</div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6" style={{ height: '400px' }}>
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* Performance Indicator */}
      <div className={`rounded-lg p-4 ${avgFPY >= 98 ? 'bg-green-50 border border-green-200' : avgFPY >= 90 ? 'bg-yellow-50 border border-yellow-200' : 'bg-red-50 border border-red-200'}`}>
        <div className={`text-sm font-medium ${avgFPY >= 98 ? 'text-green-800' : avgFPY >= 90 ? 'text-yellow-800' : 'text-red-800'}`}>
          {avgFPY >= 98 ? '✓ Excellent Quality' : avgFPY >= 90 ? '⚠ Quality Needs Attention' : '✗ Quality Issues'}
        </div>
        <div className={`text-xs mt-1 ${avgFPY >= 98 ? 'text-green-700' : avgFPY >= 90 ? 'text-yellow-700' : 'text-red-700'}`}>
          {avgFPY >= 98
            ? 'FPY is above the 98% target. Quality processes are effective!'
            : avgFPY >= 90
            ? 'FPY is below the 98% target. Review quality processes and root causes.'
            : 'FPY is significantly below target. Immediate quality improvement needed.'}
        </div>
      </div>
    </div>
  );
};

export default FPYChart;
