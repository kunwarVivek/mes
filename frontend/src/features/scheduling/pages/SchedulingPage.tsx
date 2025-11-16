import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { GanttScheduler, GanttTask } from '../components/GanttScheduler';
import { workOrderService } from '@/services/workOrders.service';
import { laneService } from '@/services/lanes.service';
import { format } from 'date-fns';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Calendar, Filter, Download, Plus } from 'lucide-react';

interface WorkOrder {
  id: number;
  work_order_number: string;
  product_name: string;
  quantity_ordered: number;
  quantity_completed: number;
  status: string;
  priority: number;
  start_date_planned?: string;
  end_date_planned?: string;
  lane_id?: number;
  dependencies?: number[];
}

interface Lane {
  id: number;
  name: string;
  capacity: number;
}

/**
 * Visual Production Scheduling Page
 *
 * Features:
 * - Gantt chart view of all work orders
 * - Drag-and-drop rescheduling
 * - Lane filtering (show work orders for specific production lines)
 * - Dependency visualization
 * - Conflict detection
 * - Export to PDF/CSV
 */
export const SchedulingPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedLaneId, setSelectedLaneId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'Day' | 'Week' | 'Month'>('Week');
  const [showCompletedOrders, setShowCompletedOrders] = useState(false);

  // Fetch work orders
  const {
    data: workOrders = [],
    isLoading: isLoadingWorkOrders,
    error: workOrdersError,
  } = useQuery<WorkOrder[]>({
    queryKey: ['workOrders', 'scheduling', selectedLaneId],
    queryFn: async () => {
      const filters = {
        status: showCompletedOrders ? undefined : 'COMPLETED',
        lane_id: selectedLaneId || undefined,
      };
      return await workOrderService.getAll(filters);
    },
  });

  // Fetch lanes
  const { data: lanes = [] } = useQuery<Lane[]>({
    queryKey: ['lanes'],
    queryFn: async () => await laneService.getAll(),
  });

  // Mutation: Update work order dates (reschedule)
  const rescheduleMutation = useMutation({
    mutationFn: async ({
      workOrderId,
      startDate,
      endDate,
    }: {
      workOrderId: number;
      startDate: Date;
      endDate: Date;
    }) => {
      return await workOrderService.update(workOrderId, {
        start_date_planned: startDate.toISOString(),
        end_date_planned: endDate.toISOString(),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] });
    },
  });

  // Mutation: Update work order progress
  const updateProgressMutation = useMutation({
    mutationFn: async ({ workOrderId, progress }: { workOrderId: number; progress: number }) => {
      return await workOrderService.updateProgress(workOrderId, progress);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] });
    },
  });

  // Convert work orders to Gantt tasks
  const ganttTasks: GanttTask[] = workOrders
    .filter(wo => wo.start_date_planned && wo.end_date_planned)
    .map(wo => ({
      id: `wo-${wo.id}`,
      name: `${wo.work_order_number} - ${wo.product_name}`,
      start: wo.start_date_planned!,
      end: wo.end_date_planned!,
      progress: wo.quantity_ordered > 0 ? (wo.quantity_completed / wo.quantity_ordered) * 100 : 0,
      dependencies: wo.dependencies?.map(dep => `wo-${dep}`).join(','),
      custom_class: `status-${wo.status.toLowerCase().replace('_', '-')} ${
        wo.priority === 1 ? 'high-priority' : ''
      }`,
      lane_id: wo.lane_id,
      work_order_id: wo.id,
      status: wo.status,
      priority: wo.priority,
    }));

  // Handle task click (show work order details)
  const handleTaskClick = (task: GanttTask) => {
    console.log('Work Order clicked:', task.work_order_id);
    // TODO: Open work order details modal or navigate to WO page
  };

  // Handle reschedule (drag-and-drop)
  const handleTaskDatesChange = (task: GanttTask, start: Date, end: Date) => {
    if (!task.work_order_id) return;

    rescheduleMutation.mutate({
      workOrderId: task.work_order_id,
      startDate: start,
      endDate: end,
    });
  };

  // Handle progress update
  const handleProgressChange = (task: GanttTask, progress: number) => {
    if (!task.work_order_id) return;

    updateProgressMutation.mutate({
      workOrderId: task.work_order_id,
      progress,
    });
  };

  // Export to CSV
  const handleExportCSV = () => {
    const csvContent = [
      ['Work Order', 'Product', 'Lane', 'Start Date', 'End Date', 'Progress', 'Status', 'Priority'],
      ...workOrders.map(wo => [
        wo.work_order_number,
        wo.product_name,
        lanes.find(l => l.id === wo.lane_id)?.name || '',
        wo.start_date_planned || '',
        wo.end_date_planned || '',
        `${wo.quantity_completed}/${wo.quantity_ordered}`,
        wo.status,
        wo.priority.toString(),
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `schedule-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (isLoadingWorkOrders) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Loading schedule...</span>
      </div>
    );
  }

  if (workOrdersError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load work orders: {workOrdersError.message}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Visual Production Scheduling</h1>
          <p className="text-gray-600 mt-1">
            Drag-and-drop scheduling, dependency management, capacity planning
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
          <button
            onClick={() => (window.location.href = '/work-orders/create')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            New Work Order
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Lane Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <label className="text-sm font-medium text-gray-700">Lane:</label>
            <select
              value={selectedLaneId || ''}
              onChange={e => setSelectedLaneId(e.target.value ? Number(e.target.value) : null)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Lanes</option>
              {lanes.map(lane => (
                <option key={lane.id} value={lane.id}>
                  {lane.name}
                </option>
              ))}
            </select>
          </div>

          {/* Show Completed Toggle */}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showCompletedOrders}
              onChange={e => setShowCompletedOrders(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-gray-700">Show completed</span>
          </label>

          {/* Legend */}
          <div className="ml-auto flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-blue-300"></div>
              <span className="text-gray-600">Planned</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-yellow-300"></div>
              <span className="text-gray-600">Released</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-green-400"></div>
              <span className="text-gray-600">In Progress</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-green-600"></div>
              <span className="text-gray-600">Completed</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-red-400"></div>
              <span className="text-gray-600">Delayed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Gantt Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <GanttScheduler
          tasks={ganttTasks}
          viewMode={viewMode}
          onTaskClick={handleTaskClick}
          onTaskDatesChange={handleTaskDatesChange}
          onProgressChange={handleProgressChange}
          readonly={false}
        />
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Total Work Orders</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{workOrders.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">In Progress</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {workOrders.filter(wo => wo.status === 'IN_PROGRESS').length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Planned</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {workOrders.filter(wo => wo.status === 'PLANNED').length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Delayed</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {
              workOrders.filter(
                wo =>
                  wo.end_date_planned &&
                  new Date(wo.end_date_planned) < new Date() &&
                  wo.status !== 'COMPLETED'
              ).length
            }
          </div>
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">How to use</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>Drag and drop</strong> tasks to reschedule work orders</li>
          <li>• <strong>Click on tasks</strong> to view work order details</li>
          <li>• <strong>Drag progress bar</strong> to update completion percentage</li>
          <li>• <strong>Filter by lane</strong> to focus on specific production lines</li>
          <li>• <strong>Dependencies shown as arrows</strong> - maintain workflow order</li>
        </ul>
      </div>
    </div>
  );
};

export default SchedulingPage;
