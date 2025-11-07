import apiClient from '@/lib/api-client'

export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at?: string
}

export interface CreateUserDto {
  email: string
  username: string
  password: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface UpdateUserDto {
  email?: string
  username?: string
  password?: string
  is_active?: boolean
}

export const userService = {
  getUsers: async (): Promise<User[]> => {
    const response = await apiClient.get('/api/v1/users/')
    return response.data
  },

  getUser: async (id: number): Promise<User> => {
    const response = await apiClient.get(`/api/v1/users/${id}`)
    return response.data
  },

  createUser: async (userData: CreateUserDto): Promise<User> => {
    const response = await apiClient.post('/api/v1/users/', userData)
    return response.data
  },

  updateUser: async (id: number, userData: UpdateUserDto): Promise<User> => {
    const response = await apiClient.put(`/api/v1/users/${id}`, userData)
    return response.data
  },

  deleteUser: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/users/${id}`)
  },
}
