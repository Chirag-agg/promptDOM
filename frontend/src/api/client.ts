export const API_BASE_URL = 'http://localhost:8000';

export const apiClient = {
  get: async (endpoint: string) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`GET ${endpoint} failed: ${response.statusText}`);
    }
    return response.json();
  },
  
  post: async (endpoint: string, data: any) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`POST ${endpoint} failed: ${response.statusText}`);
    }
    return response.json();
  },

  uploadReferenceImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/reference/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload Error: ${response.statusText}`);
    }

    return response.json();
  },
};

export const studioApi = {
  transformTest: (prompt: string, referenceId?: string) => 
    apiClient.post('/transform/test', { prompt, reference_id: referenceId }),
  generatePlan: (prompt: string, referenceId?: string) =>
    apiClient.post('/transform/plan', { prompt, reference_id: referenceId }),
  applyRedesign: (prompt: string, designPlan: any, referenceId?: string) =>
    apiClient.post('/transform/apply', { prompt, design_plan: designPlan, reference_id: referenceId }),
  uploadReference: (file: File) =>
    apiClient.uploadReferenceImage(file),
  getHistory: () =>
    apiClient.get('/history'),
  getHistoryRecord: (runId: string) =>
    apiClient.get(`/history/${runId}`),
};
