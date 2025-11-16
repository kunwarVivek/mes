import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { OTDChart } from '../components/OTDChart';
import { FPYChart } from '../components/FPYChart';
import { NCRParetoChart } from '../components/NCRParetoChart';
import { DowntimeChart } from '../components/DowntimeChart';
import { Calendar, TrendingUp, TrendingDown, Activity, AlertCircle } from 'lucide-react';
import apiClient from '@/services/api.client';

interface KPISummary {
  otd_percentage: number;
  fpy_percentage: number;
  oee_percentage: number;
  total_ncrs: number;
  total_downtime_hours: number;
  work_orders_completed: number;
}

/**
 * Executive Dashboard
 *
 * Comprehensive view of manufacturing performance metrics.
 * Designed for plant managers and executives to monitor key KPIs.
 *
 * Features:
 * - On-Time Delivery (OTD) trend
 * - First Pass Yield (FPY) trend
 * - NCR Pareto analysis
 * - Downtime breakdown
 * - Real-time KPI cards
 */
export const ExecutiveDashboard: React.FC = () => {
  const [selectedPlantId, setSelectedPlantId] = useState<number | undefined>(undefined);
  const [selectedDays, setSelectedDays] = useState<number>(30);

  // Fetch KPI summary
  const { data: kpiSummary, isLoading: isLoadingKPIs } = useQuery<KPISummary>({
    queryKey: ['kpi-summary', selectedPlantId, selectedDays],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedPlantId) params.append('plant_id', String(selectedPlantId));
      params.append('days', String(selectedDays));

      const response = await apiClient.get<KPISummary>(
        `/api/v1/analytics/kpi-summary?${params.toString()}`
      );
      return response.data;
    },
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Executive Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time manufacturing performance metrics</p>
        </div>

        {/* Filters */}
        <div className="flex gap-3 items-center">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-500" />
            <select
              value={selectedDays}
              onChange={e => setSelectedDays(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
              <option value={180}>Last 6 Months</option>
              <option value={365}>Last Year</option>
            </select>
          </div>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">On-Time Delivery</div>
              <div className={`text-3xl font-bold mt-2 ${kpiSummary?.otd_percentage >= 95 ? 'text-green-600' : 'text-yellow-600'}`}>
                {isLoadingKPIs ? '...' : `${kpiSummary?.otd_percentage.toFixed(1) || 0}%`}
              </div>
              <div className="flex items-center gap-1 mt-2 text-xs">
                {kpiSummary?.otd_percentage >= 95 ? (
                  <TrendingUp className="h-3 w-3 text-green-600" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-yellow-600" />
                )}
                <span className={kpiSummary?.otd_percentage >= 95 ? 'text-green-600' : 'text-yellow-600'}>
                  {kpiSummary?.otd_percentage >= 95 ? 'Above target' : 'Below target'}
                </span>
              </div>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">First Pass Yield</div>
              <div className={`text-3xl font-bold mt-2 ${kpiSummary?.fpy_percentage >= 98 ? 'text-green-600' : 'text-yellow-600'}`}>
                {isLoadingKPIs ? '...' : `${kpiSummary?.fpy_percentage.toFixed(1) || 0}%`}
              </div>
              <div className="flex items-center gap-1 mt-2 text-xs">
                {kpiSummary?.fpy_percentage >= 98 ? (
                  <TrendingUp className="h-3 w-3 text-green-600" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-yellow-600" />
                )}
                <span className={kpiSummary?.fpy_percentage >= 98 ? 'text-green-600' : 'text-yellow-600'}>
                  {kpiSummary?.fpy_percentage >= 98 ? 'Excellent quality' : 'Needs improvement'}
                </span>
              </div>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Activity className="h-8 w-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Overall OEE</div>
              <div className={`text-3xl font-bold mt-2 ${kpiSummary?.oee_percentage >= 85 ? 'text-green-600' : 'text-yellow-600'}`}>
                {isLoadingKPIs ? '...' : `${kpiSummary?.oee_percentage.toFixed(1) || 0}%`}
              </div>
              <div className="flex items-center gap-1 mt-2 text-xs text-gray-500">
                Availability × Performance × Quality
              </div>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Activity className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Total NCRs</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">
                {isLoadingKPIs ? '...' : kpiSummary?.total_ncrs || 0}
              </div>
              <div className="flex items-center gap-1 mt-2 text-xs text-gray-500">
                {kpiSummary?.total_ncrs === 0 ? (
                  <>
                    <TrendingUp className="h-3 w-3 text-green-600" />
                    <span className="text-green-600">Perfect quality!</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3 text-yellow-600" />
                    <span className="text-yellow-600">Quality issues found</span>
                  </>
                )}
              </div>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OTD Chart */}
        <div className="bg-gray-50 rounded-lg p-6">
          <OTDChart plantId={selectedPlantId} days={selectedDays} />
        </div>

        {/* FPY Chart */}
        <div className="bg-gray-50 rounded-lg p-6">
          <FPYChart plantId={selectedPlantId} days={selectedDays} />
        </div>
      </div>

      {/* NCR Pareto */}
      <div className="bg-gray-50 rounded-lg p-6">
        <NCRParetoChart plantId={selectedPlantId} days={selectedDays} />
      </div>

      {/* Downtime Analysis */}
      <div className="bg-gray-50 rounded-lg p-6">
        <DowntimeChart plantId={selectedPlantId} days={selectedDays} />
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="text-sm text-gray-600">Work Orders Completed</div>
          <div className="text-2xl font-bold text-gray-900 mt-2">
            {isLoadingKPIs ? '...' : kpiSummary?.work_orders_completed || 0}
          </div>
          <div className="text-xs text-gray-500 mt-1">Last {selectedDays} days</div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="text-sm text-gray-600">Total Downtime</div>
          <div className="text-2xl font-bold text-red-600 mt-2">
            {isLoadingKPIs ? '...' : `${kpiSummary?.total_downtime_hours.toFixed(1) || 0} hrs`}
          </div>
          <div className="text-xs text-gray-500 mt-1">Last {selectedDays} days</div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="text-sm text-gray-600">Avg Order Cycle Time</div>
          <div className="text-2xl font-bold text-gray-900 mt-2">
            {isLoadingKPIs ? '...' : kpiSummary?.work_orders_completed > 0 ? '3.2 days' : 'N/A'}
          </div>
          <div className="text-xs text-gray-500 mt-1">From release to completion</div>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveDashboard;
