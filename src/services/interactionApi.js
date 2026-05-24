import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach token to every request if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      // Redirect to login if needed
    }
    return Promise.reject(error);
  }
);

// ==================== INTERACTION ENDPOINTS ====================

export const getInteractions = async () => {
  try {
    const response = await apiClient.get('/interactions');
    return response.data;
  } catch (error) {
    console.error('Error fetching interactions:', error);
    throw error;
  }
};

export const getInteractionById = async (id) => {
  try {
    const response = await apiClient.get(`/interactions/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching interaction ${id}:`, error);
    throw error;
  }
};

export const createInteraction = async (interactionData) => {
  try {
    const response = await apiClient.post('/interactions', interactionData);
    return response.data;
  } catch (error) {
    console.error('Error creating interaction:', error);
    throw error;
  }
};

export const updateInteraction = async (id, interactionData) => {
  try {
    const response = await apiClient.put(`/interactions/${id}`, interactionData);
    return response.data;
  } catch (error) {
    console.error(`Error updating interaction ${id}:`, error);
    throw error;
  }
};

export const deleteInteraction = async (id) => {
  try {
    const response = await apiClient.delete(`/interactions/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting interaction ${id}:`, error);
    throw error;
  }
};

export const searchInteractions = async (drug, food) => {
  try {
    const params = new URLSearchParams();
    if (drug) params.append('drug', drug);
    if (food) params.append('food', food);

    const response = await apiClient.get(`/search?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error searching interactions:', error);
    throw error;
  }
};

// ==================== HEALTH CHECK ====================

export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('Error checking backend health:', error);
    throw error;
  }
};

export default apiClient;
