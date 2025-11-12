import apiClient from '@/lib/api-client';

export interface Supplier {
  id: number;
  organization_id: number;
  supplier_code: string;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
  postal_code?: string;
  payment_terms?: string;
  rating?: number; // 1-5
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreate {
  supplier_code: string;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
  postal_code?: string;
  payment_terms?: string;
  rating?: number;
  is_active?: boolean;
  notes?: string;
}

export interface SupplierUpdate extends Partial<SupplierCreate> {}

export interface SupplierListParams {
  skip?: number;
  limit?: number;
  search?: string;
  rating_min?: number;
  is_active?: boolean;
}

class SuppliersService {
  private readonly basePath = '/api/v1/suppliers';

  async list(params?: SupplierListParams): Promise<Supplier[]> {
    const response = await apiClient.get<Supplier[]>(this.basePath, { params });
    return response.data;
  }

  async get(id: number): Promise<Supplier> {
    const response = await apiClient.get<Supplier>(`${this.basePath}/${id}`);
    return response.data;
  }

  async create(data: SupplierCreate): Promise<Supplier> {
    const response = await apiClient.post<Supplier>(this.basePath, data);
    return response.data;
  }

  async update(id: number, data: SupplierUpdate): Promise<Supplier> {
    const response = await apiClient.put<Supplier>(`${this.basePath}/${id}`, data);
    return response.data;
  }

  async delete(id: number): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  async rate(id: number, rating: number): Promise<void> {
    await apiClient.post(`${this.basePath}/${id}/rate`, null, {
      params: { rating }
    });
  }

  async getMaterials(id: number): Promise<any[]> {
    const response = await apiClient.get(`${this.basePath}/${id}/materials`);
    return response.data.materials || [];
  }
}

export const suppliersService = new SuppliersService();
export default suppliersService;
