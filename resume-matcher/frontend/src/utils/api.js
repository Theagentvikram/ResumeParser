import axios from 'axios';

// Base URL for API requests
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get all resumes
export const getAllResumes = async () => {
  try {
    const response = await api.get('/resumes');
    return response.data;
  } catch (error) {
    console.error('Error fetching resumes:', error);
    throw error;
  }
};

// Get a single resume by ID
export const getResumeById = async (id) => {
  try {
    const response = await api.get(`/resumes/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching resume ${id}:`, error);
    throw error;
  }
};

// Upload a single resume
export const uploadResume = async (file, onUploadProgress) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/resumes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    
    return response.data;
  } catch (error) {
    console.error('Error uploading resume:', error);
    throw error;
  }
};

// Upload multiple resumes
export const uploadBulkResumes = async (files, onUploadProgress) => {
  try {
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post('/resumes/upload-bulk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    
    return response.data;
  } catch (error) {
    console.error('Error uploading resumes:', error);
    throw error;
  }
};

// Search resumes
export const searchResumes = async (query, filters = {}) => {
  try {
    const response = await api.post('/resumes/search', {
      query,
      filters,
    });
    
    return response.data;
  } catch (error) {
    console.error('Error searching resumes:', error);
    throw error;
  }
};

// Get all skills
export const getAllSkills = async () => {
  try {
    const response = await api.get('/skills');
    return response.data;
  } catch (error) {
    console.error('Error fetching skills:', error);
    throw error;
  }
};

// Delete a resume
export const deleteResume = async (id) => {
  try {
    const response = await api.delete(`/resumes/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting resume ${id}:`, error);
    throw error;
  }
};

// Download a resume
export const downloadResume = (id) => {
  window.open(`${API_URL}/resumes/${id}/download`, '_blank');
};

// Analyze resume text
export const analyzeResumeText = async (text) => {
  try {
    const response = await api.post('/resumes/analyze', { text });
    return response.data;
  } catch (error) {
    console.error('Error analyzing resume text:', error);
    throw error;
  }
};

export default api;
