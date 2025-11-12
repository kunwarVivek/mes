import React, { useState, useEffect } from 'react';
import { ArrowDownCircle, ArrowUpCircle, RefreshCw, TrendingUp, DollarSign } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface MaterialTransaction {
  id: number;
  material_id: number;
  material_code: string;
  material_name: string;
  transaction_type: 'receipt' | 'issue' | 'adjustment' | 'transfer_in' | 'transfer_out';
  quantity: number;
  unit_cost: number | null;
  total_cost: number | null;
  reference_type: string | null;
  reference_id: number | null;
  batch_number: string | null;
  lot_number: string | null;
  transaction_date: string;
  performed_by: string | null;
}

export const MaterialTransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<MaterialTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [transactionTypeFilter, setTransactionTypeFilter] = useState<string>('all');
  const [materialSearch, setMaterialSearch] = useState('');

  // Mock data for demonstration (replace with actual API call)
  useEffect(() => {
    loadTransactions();
  }, [transactionTypeFilter, materialSearch]);

  const loadTransactions = async () => {
    setLoading(true);
    // TODO: Replace with actual API call
    // const data = await materialTransactionsService.list({ type: transactionTypeFilter, search: materialSearch });

    // Mock data
    setTimeout(() => {
      setTransactions([
        {
          id: 1,
          material_id: 101,
          material_code: 'MAT-001',
          material_name: 'Steel Plate 10mm',
          transaction_type: 'receipt',
          quantity: 100,
          unit_cost: 25.50,
          total_cost: 2550.00,
          reference_type: 'purchase_order',
          reference_id: 1001,
          batch_number: 'BATCH-2024-001',
          lot_number: null,
          transaction_date: new Date().toISOString(),
          performed_by: 'John Doe',
        },
        {
          id: 2,
          material_id: 101,
          material_code: 'MAT-001',
          material_name: 'Steel Plate 10mm',
          transaction_type: 'issue',
          quantity: -30,
          unit_cost: 25.50,
          total_cost: -765.00,
          reference_type: 'work_order',
          reference_id: 5001,
          batch_number: 'BATCH-2024-001',
          lot_number: null,
          transaction_date: new Date(Date.now() - 86400000).toISOString(),
          performed_by: 'Jane Smith',
        },
      ]);
      setLoading(false);
    }, 500);
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'receipt':
      case 'transfer_in':
        return <ArrowDownCircle className="h-4 w-4 text-green-600" />;
      case 'issue':
      case 'transfer_out':
        return <ArrowUpCircle className="h-4 w-4 text-red-600" />;
      case 'adjustment':
        return <RefreshCw className="h-4 w-4 text-blue-600" />;
      default:
        return null;
    }
  };

  const getTransactionBadgeVariant = (type: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (type) {
      case 'receipt':
      case 'transfer_in':
        return 'default';
      case 'issue':
      case 'transfer_out':
        return 'destructive';
      case 'adjustment':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const formatCurrency = (amount: number | null) => {
    if (amount === null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate summary stats
  const totalReceipts = transactions
    .filter(t => t.transaction_type === 'receipt' || t.transaction_type === 'transfer_in')
    .reduce((sum, t) => sum + Math.abs(t.quantity), 0);

  const totalIssues = transactions
    .filter(t => t.transaction_type === 'issue' || t.transaction_type === 'transfer_out')
    .reduce((sum, t) => sum + Math.abs(t.quantity), 0);

  const totalValue = transactions
    .reduce((sum, t) => sum + (t.total_cost || 0), 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Material Transactions</h1>
        <p className="text-gray-500">Track all inventory movements and costing</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Receipts</CardTitle>
            <ArrowDownCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{totalReceipts.toFixed(2)}</div>
            <p className="text-xs text-gray-500">Units received</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Issues</CardTitle>
            <ArrowUpCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{totalIssues.toFixed(2)}</div>
            <p className="text-xs text-gray-500">Units issued</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Net Inventory Value</CardTitle>
            <DollarSign className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(totalValue)}</div>
            <p className="text-xs text-gray-500">Current value</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Material Search</Label>
              <Input
                placeholder="Search material code or name..."
                value={materialSearch}
                onChange={(e) => setMaterialSearch(e.target.value)}
              />
            </div>

            <div>
              <Label>Transaction Type</Label>
              <Select value={transactionTypeFilter} onValueChange={setTransactionTypeFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="receipt">Receipts Only</SelectItem>
                  <SelectItem value="issue">Issues Only</SelectItem>
                  <SelectItem value="adjustment">Adjustments Only</SelectItem>
                  <SelectItem value="transfer_in">Transfers In</SelectItem>
                  <SelectItem value="transfer_out">Transfers Out</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Date Range</Label>
              <Select defaultValue="7days">
                <SelectTrigger>
                  <SelectValue placeholder="Select range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="7days">Last 7 Days</SelectItem>
                  <SelectItem value="30days">Last 30 Days</SelectItem>
                  <SelectItem value="90days">Last 90 Days</SelectItem>
                  <SelectItem value="all">All Time</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History ({transactions.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Material</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead className="text-right">Unit Cost</TableHead>
                <TableHead className="text-right">Total Cost</TableHead>
                <TableHead>Batch/Lot</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Performed By</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    Loading transactions...
                  </TableCell>
                </TableRow>
              ) : transactions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                    No transactions found for the selected filters.
                  </TableCell>
                </TableRow>
              ) : (
                transactions.map((transaction) => (
                  <TableRow key={transaction.id}>
                    <TableCell className="text-sm">
                      {formatDate(transaction.transaction_date)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={getTransactionBadgeVariant(transaction.transaction_type)}
                        className="flex items-center gap-1 w-fit"
                      >
                        {getTransactionIcon(transaction.transaction_type)}
                        {transaction.transaction_type.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{transaction.material_code}</div>
                      <div className="text-sm text-gray-500">{transaction.material_name}</div>
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        transaction.quantity > 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {transaction.quantity > 0 ? '+' : ''}
                      {transaction.quantity.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(transaction.unit_cost)}
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        transaction.total_cost && transaction.total_cost > 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {formatCurrency(transaction.total_cost)}
                    </TableCell>
                    <TableCell>
                      {transaction.batch_number && (
                        <div className="text-sm">
                          <div>Batch: {transaction.batch_number}</div>
                        </div>
                      )}
                      {transaction.lot_number && (
                        <div className="text-sm text-gray-500">Lot: {transaction.lot_number}</div>
                      )}
                      {!transaction.batch_number && !transaction.lot_number && '-'}
                    </TableCell>
                    <TableCell>
                      {transaction.reference_type && transaction.reference_id ? (
                        <div className="text-sm">
                          <div className="capitalize">{transaction.reference_type.replace('_', ' ')}</div>
                          <div className="text-gray-500">#{transaction.reference_id}</div>
                        </div>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell className="text-sm">{transaction.performed_by || '-'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* FIFO/LIFO Costing Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Costing Method Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p>
              <strong>Current Method:</strong> FIFO (First In, First Out)
            </p>
            <p className="text-gray-600">
              Inventory is valued using the oldest costs first. This table shows all material
              movements with their respective costs for accurate inventory valuation.
            </p>
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-900">
                <strong>Tip:</strong> Material transactions are stored in a TimescaleDB hypertable
                for efficient time-series queries. Historical costing data is compressed after 7
                days and retained for 3 years.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MaterialTransactionsPage;
