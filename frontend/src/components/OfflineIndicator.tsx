import React, { useState, useEffect } from 'react';
import { WifiOff, Wifi, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

interface QueuedAction {
  id: string;
  type: string;
  data: any;
  timestamp: number;
  retries: number;
}

export const OfflineIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [queuedActions, setQueuedActions] = useState<QueuedAction[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  useEffect(() => {
    // Load queued actions from localStorage
    loadQueue();

    // Listen for online/offline events
    const handleOnline = () => {
      setIsOnline(true);
      // Auto-sync when coming back online
      syncQueue();
    };

    const handleOffline = () => {
      setIsOnline(false);
      setSyncError(null);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Periodic queue check
    const interval = setInterval(() => {
      loadQueue();
    }, 5000); // Check every 5 seconds

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const loadQueue = () => {
    try {
      const stored = localStorage.getItem('offline_queue');
      if (stored) {
        const queue = JSON.parse(stored);
        setQueuedActions(queue);
      }
    } catch (err) {
      console.error('Failed to load offline queue:', err);
    }
  };

  const syncQueue = async () => {
    if (queuedActions.length === 0) return;

    setIsSyncing(true);
    setSyncError(null);

    try {
      const failedActions: QueuedAction[] = [];

      // Process each queued action
      for (const action of queuedActions) {
        try {
          await processAction(action);
        } catch (err) {
          console.error('Failed to sync action:', action, err);

          // Increment retry count
          action.retries = (action.retries || 0) + 1;

          // Keep in queue if retries < 3
          if (action.retries < 3) {
            failedActions.push(action);
          }
        }
      }

      // Update queue with only failed actions
      const newQueue = failedActions;
      localStorage.setItem('offline_queue', JSON.stringify(newQueue));
      setQueuedActions(newQueue);

      if (newQueue.length === 0) {
        setLastSyncTime(new Date());
      } else {
        setSyncError(`${newQueue.length} items failed to sync. Will retry.`);
      }
    } catch (err: any) {
      console.error('Sync failed:', err);
      setSyncError('Sync failed. Please try again.');
    } finally {
      setIsSyncing(false);
    }
  };

  const processAction = async (action: QueuedAction): Promise<void> => {
    // This would integrate with your API client
    // For now, just simulate the sync
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        // Simulate success/failure
        if (Math.random() > 0.1) {
          resolve();
        } else {
          reject(new Error('Sync failed'));
        }
      }, 500);
    });
  };

  const clearQueue = () => {
    localStorage.removeItem('offline_queue');
    setQueuedActions([]);
    setSyncError(null);
  };

  // Don't show if online and no queued actions
  if (isOnline && queuedActions.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 max-w-sm">
      <Alert
        className={`shadow-lg ${
          isOnline
            ? queuedActions.length > 0
              ? 'bg-yellow-50 border-yellow-500'
              : 'bg-green-50 border-green-500'
            : 'bg-orange-50 border-orange-500'
        }`}
      >
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="flex-shrink-0">
            {isOnline ? (
              queuedActions.length > 0 ? (
                <RefreshCw
                  className={`h-5 w-5 text-yellow-600 ${isSyncing ? 'animate-spin' : ''}`}
                />
              ) : (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              )
            ) : (
              <WifiOff className="h-5 w-5 text-orange-600" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-sm">
                {isOnline ? (
                  queuedActions.length > 0 ? (
                    'Sync Pending'
                  ) : (
                    'All Synced'
                  )
                ) : (
                  'Offline Mode'
                )}
              </div>

              <Badge
                variant={isOnline ? 'default' : 'secondary'}
                className="ml-2"
              >
                {isOnline ? (
                  <><Wifi className="h-3 w-3 mr-1" /> Online</>
                ) : (
                  <><WifiOff className="h-3 w-3 mr-1" /> Offline</>
                )}
              </Badge>
            </div>

            <AlertDescription className="text-sm">
              {isOnline ? (
                queuedActions.length > 0 ? (
                  <>
                    {queuedActions.length} {queuedActions.length === 1 ? 'item' : 'items'}{' '}
                    waiting to sync
                    {lastSyncTime && (
                      <div className="text-xs text-gray-500 mt-1">
                        Last synced: {lastSyncTime.toLocaleTimeString()}
                      </div>
                    )}
                  </>
                ) : (
                  'All changes synced successfully'
                )
              ) : (
                <>
                  You're offline. Changes will sync when you reconnect.
                  {queuedActions.length > 0 && (
                    <div className="mt-1">
                      <strong>{queuedActions.length}</strong> {queuedActions.length === 1 ? 'change' : 'changes'} queued
                    </div>
                  )}
                </>
              )}
            </AlertDescription>

            {/* Sync Error */}
            {syncError && (
              <div className="flex items-start gap-2 text-sm text-red-700 bg-red-100 p-2 rounded">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>{syncError}</span>
              </div>
            )}

            {/* Action Buttons */}
            {queuedActions.length > 0 && (
              <div className="flex gap-2 mt-2">
                <Button
                  size="sm"
                  onClick={syncQueue}
                  disabled={!isOnline || isSyncing}
                  className="flex-1"
                >
                  <RefreshCw className={`h-3 w-3 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
                  {isSyncing ? 'Syncing...' : 'Sync Now'}
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={clearQueue}
                  disabled={isSyncing}
                  className="flex-1"
                >
                  Clear Queue
                </Button>
              </div>
            )}
          </div>
        </div>
      </Alert>
    </div>
  );
};

export default OfflineIndicator;
