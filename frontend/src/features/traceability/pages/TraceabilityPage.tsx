import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import apiClient from '@/services/api.client';

/**
 * Traceability Page
 *
 * Lot and serial number tracking with forward/backward genealogy.
 * Supports recall investigations and compliance audits.
 */
export const TraceabilityPage: React.FC = () => {
  const [searchType, setSearchType] = useState<'lot' | 'serial'>('lot');
  const [searchValue, setSearchValue] = useState('');
  const [traceDirection, setTraceDirection] = useState<'forward' | 'backward'>('forward');

  const { data: traceResults, isLoading, refetch } = useQuery({
    queryKey: ['traceability', searchType, searchValue, traceDirection],
    queryFn: async () => {
      if (!searchValue) return null;
      const response = await apiClient.get(
        `/api/v1/traceability/${searchType}/${searchValue}/trace-${traceDirection}`
      );
      return response.data;
    },
    enabled: false,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue) {
      refetch();
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Traceability</h1>
        <p className="text-gray-600 mt-1">
          Lot and serial number tracking with forward/backward genealogy
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Type
              </label>
              <select
                value={searchType}
                onChange={e => setSearchType(e.target.value as 'lot' | 'serial')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="lot">Lot Number</option>
                <option value="serial">Serial Number</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {searchType === 'lot' ? 'Lot Number' : 'Serial Number'}
              </label>
              <input
                type="text"
                value={searchValue}
                onChange={e => setSearchValue(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={searchType === 'lot' ? 'LOT-2025-001' : 'SN-ABC12345'}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trace Direction
              </label>
              <select
                value={traceDirection}
                onChange={e => setTraceDirection(e.target.value as 'forward' | 'backward')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="forward">Forward (→ Customers)</option>
                <option value="backward">Backward (← Materials)</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <Search className="h-4 w-4" />
            {isLoading ? 'Searching...' : 'Search Genealogy'}
          </button>
        </form>
      </div>

      {/* Results */}
      {traceResults && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {traceDirection === 'forward' ? 'Forward Trace Results' : 'Backward Trace Results'}
          </h2>
          <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto">
            {JSON.stringify(traceResults, null, 2)}
          </pre>
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">How to use</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>Forward Trace:</strong> Find which customers received products from a specific lot/serial</li>
          <li>• <strong>Backward Trace:</strong> Find which materials/lots were used to create a product</li>
          <li>• <strong>Recall Investigation:</strong> Use forward trace to identify affected customers</li>
          <li>• <strong>Root Cause Analysis:</strong> Use backward trace to find defective material sources</li>
        </ul>
      </div>
    </div>
  );
};

export default TraceabilityPage;
