import React, { useState, useEffect } from 'react';
import { Plus, Search, Edit, Trash2, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';
import suppliersService, { Supplier, SupplierCreate } from '@/services/suppliers.service';

export const SuppliersPage: React.FC = () => {
  const { toast } = useToast();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [ratingFilter, setRatingFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [formData, setFormData] = useState<Partial<SupplierCreate>>({
    supplier_code: '',
    name: '',
    is_active: true,
  });

  useEffect(() => {
    loadSuppliers();
  }, [searchTerm, ratingFilter, statusFilter]);

  const loadSuppliers = async () => {
    setLoading(true);
    try {
      const params: any = {};

      if (searchTerm) params.search = searchTerm;
      if (ratingFilter !== 'all') params.rating_min = parseInt(ratingFilter);
      if (statusFilter !== 'all') params.is_active = statusFilter === 'active';

      const data = await suppliersService.list(params);
      setSuppliers(data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load suppliers',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingSupplier(null);
    setFormData({
      supplier_code: '',
      name: '',
      is_active: true,
    });
    setIsDialogOpen(true);
  };

  const handleEdit = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setFormData(supplier);
    setIsDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editingSupplier) {
        await suppliersService.update(editingSupplier.id, formData);
        toast({ title: 'Success', description: 'Supplier updated successfully' });
      } else {
        await suppliersService.create(formData as SupplierCreate);
        toast({ title: 'Success', description: 'Supplier created successfully' });
      }

      setIsDialogOpen(false);
      loadSuppliers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save supplier',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this supplier?')) return;

    try {
      await suppliersService.delete(id);
      toast({ title: 'Success', description: 'Supplier deleted successfully' });
      loadSuppliers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete supplier',
        variant: 'destructive',
      });
    }
  };

  const handleRate = async (id: number, rating: number) => {
    try {
      await suppliersService.rate(id, rating);
      toast({ title: 'Success', description: 'Supplier rated successfully' });
      loadSuppliers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to rate supplier',
        variant: 'destructive',
      });
    }
  };

  const renderStars = (rating: number | undefined, supplierId: number) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 cursor-pointer transition-colors ${
              rating && star <= rating
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-gray-300'
            }`}
            onClick={() => handleRate(supplierId, star)}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Suppliers</h1>
          <p className="text-gray-500">Manage your material suppliers and vendors</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Add Supplier
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search suppliers..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <Select value={ratingFilter} onValueChange={setRatingFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by rating" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Ratings</SelectItem>
                <SelectItem value="5">5 Stars</SelectItem>
                <SelectItem value="4">4+ Stars</SelectItem>
                <SelectItem value="3">3+ Stars</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active Only</SelectItem>
                <SelectItem value="inactive">Inactive Only</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Suppliers List ({suppliers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Payment Terms</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : suppliers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                    No suppliers found. Create your first supplier to get started.
                  </TableCell>
                </TableRow>
              ) : (
                suppliers.map((supplier) => (
                  <TableRow key={supplier.id}>
                    <TableCell className="font-medium">{supplier.supplier_code}</TableCell>
                    <TableCell>{supplier.name}</TableCell>
                    <TableCell>
                      {supplier.contact_person && (
                        <div className="text-sm">
                          <div>{supplier.contact_person}</div>
                          {supplier.email && (
                            <div className="text-gray-500">{supplier.email}</div>
                          )}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      {supplier.city && (
                        <div className="text-sm">
                          {supplier.city}
                          {supplier.country && `, ${supplier.country}`}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>{renderStars(supplier.rating, supplier.id)}</TableCell>
                    <TableCell>{supplier.payment_terms || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={supplier.is_active ? 'default' : 'secondary'}>
                        {supplier.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEdit(supplier)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete(supplier.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingSupplier ? 'Edit Supplier' : 'Create New Supplier'}
            </DialogTitle>
            <DialogDescription>
              {editingSupplier
                ? 'Update supplier information'
                : 'Add a new supplier to your system'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-4">
            {/* Supplier Code */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="supplier_code">Supplier Code *</Label>
              <Input
                id="supplier_code"
                value={formData.supplier_code || ''}
                onChange={(e) => setFormData({ ...formData, supplier_code: e.target.value })}
                placeholder="SUP001"
              />
            </div>

            {/* Name */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="name">Supplier Name *</Label>
              <Input
                id="name"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Acme Corporation"
              />
            </div>

            {/* Contact Person */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="contact_person">Contact Person</Label>
              <Input
                id="contact_person"
                value={formData.contact_person || ''}
                onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                placeholder="John Doe"
              />
            </div>

            {/* Email */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="contact@supplier.com"
              />
            </div>

            {/* Phone */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+1 234 567 8900"
              />
            </div>

            {/* City */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                value={formData.city || ''}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                placeholder="New York"
              />
            </div>

            {/* Country */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="country">Country</Label>
              <Input
                id="country"
                value={formData.country || ''}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                placeholder="USA"
              />
            </div>

            {/* Postal Code */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="postal_code">Postal Code</Label>
              <Input
                id="postal_code"
                value={formData.postal_code || ''}
                onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                placeholder="10001"
              />
            </div>

            {/* Payment Terms */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="payment_terms">Payment Terms</Label>
              <Select
                value={formData.payment_terms || ''}
                onValueChange={(value) => setFormData({ ...formData, payment_terms: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select payment terms" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Net 30">Net 30</SelectItem>
                  <SelectItem value="Net 60">Net 60</SelectItem>
                  <SelectItem value="Net 90">Net 90</SelectItem>
                  <SelectItem value="Due on Receipt">Due on Receipt</SelectItem>
                  <SelectItem value="COD">COD (Cash on Delivery)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Rating */}
            <div className="col-span-2 md:col-span-1">
              <Label htmlFor="rating">Rating (1-5)</Label>
              <Select
                value={formData.rating?.toString() || ''}
                onValueChange={(value) => setFormData({ ...formData, rating: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select rating" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">⭐⭐⭐⭐⭐ (5 stars)</SelectItem>
                  <SelectItem value="4">⭐⭐⭐⭐ (4 stars)</SelectItem>
                  <SelectItem value="3">⭐⭐⭐ (3 stars)</SelectItem>
                  <SelectItem value="2">⭐⭐ (2 stars)</SelectItem>
                  <SelectItem value="1">⭐ (1 star)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Address */}
            <div className="col-span-2">
              <Label htmlFor="address">Address</Label>
              <Textarea
                id="address"
                value={formData.address || ''}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                placeholder="123 Main Street, Suite 100"
                rows={2}
              />
            </div>

            {/* Notes */}
            <div className="col-span-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Any additional notes about this supplier"
                rows={3}
              />
            </div>

            {/* Active Status */}
            <div className="col-span-2 flex items-center justify-between p-4 border rounded-lg">
              <div>
                <Label htmlFor="is_active">Active Status</Label>
                <p className="text-sm text-gray-500">
                  Inactive suppliers will not appear in selection lists
                </p>
              </div>
              <Switch
                id="is_active"
                checked={formData.is_active ?? true}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave}>
              {editingSupplier ? 'Update' : 'Create'} Supplier
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SuppliersPage;
