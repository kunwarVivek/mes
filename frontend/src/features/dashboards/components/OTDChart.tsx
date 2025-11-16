import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Line } from 'react-chartjs-2';
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
} from 'chart.js';
import { format, subDays } from 'date-fns';
import apiClient from '@/services/api.client';

// Register Chart.js components
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

interface OTDData {
  date: string;
  total_completed: number;
  on_time: number;
  late: number;
  otd_percentage: number;
}

interface OTDChartProps {
  plantId?: number;
  days?: number;
}

/**
 * On-Time Delivery (OTD) Chart
 *
 * Displays trend of on-time deliveries vs late deliveries.
 * Key metric for customer satisfaction and manufacturing efficiency.
 */
export const OTDChart: React.FC<OTDChartProps> = ({ plantId, days = 30 }) => {
  const { data, isLoading, error } = useQuery<OTDData[]>({
    queryKey: ['otd-data', plantId, days],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (plantId) params.append('plant_id', String(plantId));
      params.append('days', String(days));

      const response = await apiClient.get<OTDData[]>(
        `/api/v1/analytics/otd?${params.toString()}`
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
        Failed to load OTD data: {error.message}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        <p>No OTD data available for the selected period</p>
      </div>
    );
  }

  // Calculate summary metrics
  const totalCompleted = data.reduce((sum, d) => sum + d.total_completed, 0);
  const totalOnTime = data.reduce((sum, d) => sum + d.on_time, 0);
  const totalLate = data.reduce((sum, d) => sum + d.late, 0);
  const avgOTD = totalCompleted > 0 ? (totalOnTime / totalCompleted) * 100 : 0;

  // Prepare chart data
  const chartData = {
    labels: data.map(d => format(new Date(d.date), 'MMM dd')),
    datasets: [
      {
        label: 'OTD %',
        data: data.map(d => d.otd_percentage),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Target (95%)',
        data: Array(data.length).fill(95),
        borderColor: 'rgb(59, 130, 246)',
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
        text: 'On-Time Delivery Trend',
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
          text: 'On-Time Delivery %',
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
          <div className="text-sm text-gray-600">Average OTD</div>
          <div className={`text-2xl font-bold mt-1 ${avgOTD >= 95 ? 'text-green-600' : avgOTD >= 85 ? 'text-yellow-600' : 'text-red-600'}`}>
            {avgOTD.toFixed(1)}%
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Completed</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{totalCompleted}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">On Time</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{totalOnTime}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Late</div>
          <div className="text-2xl font-bold text-red-600 mt-1">{totalLate}</div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6" style={{ height: '400px' }}>
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* Performance Indicator */}
      <div className={`rounded-lg p-4 ${avgOTD >= 95 ? 'bg-green-50 border border-green-200' : avgOTD >= 85 ? 'bg-yellow-50 border border-yellow-200' : 'bg-red-50 border border-red-200'}`}>
        <div className={`text-sm font-medium ${avgOTD >= 95 ? 'text-green-800' : avgOTD >= 85 ? 'text-yellow-800' : 'text-red-800'}`}>
          {avgOTD >= 95 ? '✓ Excellent Performance' : avgOTD >= 85 ? '⚠ Needs Improvement' : '✗ Below Target'}
        </div>
        <div className={`text-xs mt-1 ${avgOTD >= 95 ? 'text-green-700' : avgOTD >= 85 ? 'text-yellow-700' : 'text-red-700'}`}>
          {avgOTD >= 95
            ? 'OTD is above the 95% target. Keep up the excellent work!'
            : avgOTD >= 85
            ? 'OTD is below the 95% target. Focus on reducing late deliveries.'
            : 'OTD is significantly below target. Immediate action required.'}
        </div>
      </div>
    </div>
  );
};

export default OTDChart;
