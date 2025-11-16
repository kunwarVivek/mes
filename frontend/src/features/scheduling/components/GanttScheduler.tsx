import React, { useEffect, useRef, useState } from 'react';
import Gantt from 'frappe-gantt';
import { format, addDays } from 'date-fns';
import 'frappe-gantt/dist/frappe-gantt.css';

export interface GanttTask {
  id: string;
  name: string;
  start: string; // ISO date string
  end: string; // ISO date string
  progress: number; // 0-100
  dependencies?: string; // comma-separated task IDs
  custom_class?: string;
  lane_id?: number;
  work_order_id?: number;
  status?: string;
  priority?: number;
}

interface GanttSchedulerProps {
  tasks: GanttTask[];
  viewMode?: 'Quarter Day' | 'Half Day' | 'Day' | 'Week' | 'Month';
  onTaskClick?: (task: GanttTask) => void;
  onTaskDatesChange?: (task: GanttTask, start: Date, end: Date) => void;
  onProgressChange?: (task: GanttTask, progress: number) => void;
  readonly?: boolean;
}

/**
 * Gantt Scheduler Component
 *
 * Features:
 * - Visual timeline view of work orders
 * - Drag-and-drop rescheduling
 * - Dependency visualization (arrows)
 * - Progress tracking
 * - Color-coded by status
 * - Zoom levels (day, week, month)
 */
export const GanttScheduler: React.FC<GanttSchedulerProps> = ({
  tasks,
  viewMode = 'Day',
  onTaskClick,
  onTaskDatesChange,
  onProgressChange,
  readonly = false,
}) => {
  const ganttContainerRef = useRef<HTMLDivElement>(null);
  const ganttInstanceRef = useRef<Gantt | null>(null);
  const [currentViewMode, setCurrentViewMode] = useState<string>(viewMode);

  useEffect(() => {
    if (!ganttContainerRef.current || tasks.length === 0) return;

    // Destroy previous instance
    if (ganttInstanceRef.current) {
      ganttInstanceRef.current = null;
    }

    // Create new Gantt instance
    try {
      ganttInstanceRef.current = new Gantt(ganttContainerRef.current, tasks, {
        view_mode: currentViewMode,
        date_format: 'YYYY-MM-DD',
        custom_popup_html: (task: any) => {
          const taskObj = tasks.find(t => t.id === task.id);
          return `
            <div class="gantt-popup">
              <div class="title">${task.name}</div>
              <div class="details">
                <div><strong>Start:</strong> ${format(new Date(task._start), 'MMM dd, yyyy')}</div>
                <div><strong>End:</strong> ${format(new Date(task._end), 'MMM dd, yyyy')}</div>
                <div><strong>Progress:</strong> ${task.progress}%</div>
                ${taskObj?.status ? `<div><strong>Status:</strong> ${taskObj.status}</div>` : ''}
                ${taskObj?.priority ? `<div><strong>Priority:</strong> ${taskObj.priority}</div>` : ''}
              </div>
            </div>
          `;
        },
        on_click: (task: any) => {
          const taskObj = tasks.find(t => t.id === task.id);
          if (taskObj && onTaskClick) {
            onTaskClick(taskObj);
          }
        },
        on_date_change: readonly ? undefined : (task: any, start: Date, end: Date) => {
          const taskObj = tasks.find(t => t.id === task.id);
          if (taskObj && onTaskDatesChange) {
            onTaskDatesChange(taskObj, start, end);
          }
        },
        on_progress_change: readonly ? undefined : (task: any, progress: number) => {
          const taskObj = tasks.find(t => t.id === task.id);
          if (taskObj && onProgressChange) {
            onProgressChange(taskObj, progress);
          }
        },
        arrow_curve: 5,
        bar_height: 30,
        bar_corner_radius: 3,
        padding: 18,
        view_modes: ['Quarter Day', 'Half Day', 'Day', 'Week', 'Month'],
      });
    } catch (error) {
      console.error('Failed to initialize Gantt chart:', error);
    }

    return () => {
      if (ganttInstanceRef.current) {
        ganttInstanceRef.current = null;
      }
    };
  }, [tasks, currentViewMode, onTaskClick, onTaskDatesChange, onProgressChange, readonly]);

  const handleViewModeChange = (mode: string) => {
    setCurrentViewMode(mode);
    if (ganttInstanceRef.current) {
      ganttInstanceRef.current.change_view_mode(mode);
    }
  };

  return (
    <div className="gantt-scheduler">
      {/* View Mode Controls */}
      <div className="gantt-controls flex gap-2 mb-4">
        {['Quarter Day', 'Half Day', 'Day', 'Week', 'Month'].map(mode => (
          <button
            key={mode}
            onClick={() => handleViewModeChange(mode)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              currentViewMode === mode
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {mode}
          </button>
        ))}
      </div>

      {/* Gantt Chart Container */}
      <div
        ref={ganttContainerRef}
        className="gantt-container bg-white rounded-lg shadow-sm border border-gray-200 overflow-auto"
        style={{ minHeight: '500px' }}
      />

      {tasks.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No work orders scheduled</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating a work order.</p>
        </div>
      )}

      {/* Custom CSS for Gantt styling */}
      <style jsx>{`
        .gantt-container :global(.bar) {
          cursor: ${readonly ? 'pointer' : 'move'} !important;
        }

        .gantt-container :global(.bar-progress) {
          fill: #3b82f6 !important;
        }

        .gantt-container :global(.bar-wrapper:hover .bar-progress) {
          fill: #2563eb !important;
        }

        .gantt-container :global(.bar-label) {
          fill: #ffffff !important;
          font-weight: 500 !important;
        }

        /* Status-based colors */
        .gantt-container :global(.bar.status-planned) {
          fill: #93c5fd !important;
        }

        .gantt-container :global(.bar.status-released) {
          fill: #fde047 !important;
        }

        .gantt-container :global(.bar.status-in-progress) {
          fill: #4ade80 !important;
        }

        .gantt-container :global(.bar.status-completed) {
          fill: #22c55e !important;
        }

        .gantt-container :global(.bar.status-delayed) {
          fill: #f87171 !important;
        }

        .gantt-container :global(.bar.high-priority) {
          stroke: #dc2626 !important;
          stroke-width: 3 !important;
        }

        /* Dependency arrows */
        .gantt-container :global(.arrow) {
          stroke: #9ca3af !important;
          stroke-width: 1.5 !important;
        }

        /* Popup styling */
        :global(.gantt-popup) {
          padding: 12px;
        }

        :global(.gantt-popup .title) {
          font-weight: 600;
          font-size: 14px;
          margin-bottom: 8px;
          color: #111827;
        }

        :global(.gantt-popup .details) {
          font-size: 12px;
          color: #6b7280;
        }

        :global(.gantt-popup .details > div) {
          margin-bottom: 4px;
        }

        :global(.gantt-popup strong) {
          font-weight: 500;
          color: #374151;
        }
      `}</style>
    </div>
  );
};

export default GanttScheduler;
