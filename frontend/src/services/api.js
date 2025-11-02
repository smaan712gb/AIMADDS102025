import axios from 'axios';

// Use environment variable or fallback to deployed backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://aimadds-backend-zex5qoe5gq-uc.a.run.app/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  
  register: async (email, password, role = 'user') => {
    const response = await api.post('/auth/register', { email, password, role });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Analysis endpoints
export const analysisAPI = {
  startAnalysis: async (data) => {
    const response = await api.post('/analysis/start', data);
    return response.data;
  },
  
  getProgress: async (jobId) => {
    const response = await api.get(`/analysis/${jobId}/progress`);
    return response.data;
  },
  
  getResult: async (jobId) => {
    const response = await api.get(`/analysis/${jobId}/result`);
    return response.data;
  },
  
  listAnalyses: async () => {
    const response = await api.get('/analysis/list');
    return response.data;
  },
  
  downloadReport: async (jobId, fileType) => {
    // Map revolutionary file types to their actual paths
    const fileExtensions = {
      'revolutionary_excel': 'xlsx',
      'revolutionary_ppt': 'pptx',
      'revolutionary_pdf': 'pdf',
      'excel': 'xlsx',
      'pptx': 'pptx',
      'pdf': 'pdf'
    };
    
    const extension = fileExtensions[fileType] || fileType;
    
    try {
      const response = await api.get(`/analysis/${jobId}/download/${fileType}`, {
        responseType: 'blob',
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${jobId}.${extension}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },
};

// WebSocket connection
export const createWebSocket = (jobId, onMessage) => {
  // Use environment variable or fallback to deployed backend
  const wsBaseUrl = import.meta.env.VITE_WS_URL || 'wss://aimadds-backend-zex5qoe5gq-uc.a.run.app';
  const wsUrl = `${wsBaseUrl}/ws/analysis/${jobId}`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  return ws;
};

export default api;
