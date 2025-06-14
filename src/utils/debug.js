// Debug utility to log environment variables and API configuration
export function logEnvConfig() {
  console.log('Environment Variables:', {
    NODE_ENV: import.meta.env.MODE,
    VITE_API_URL: import.meta.env.VITE_API_URL,
    VITE_ENABLE_MOCK_DATA: import.meta.env.VITE_ENABLE_MOCK_DATA,
    ANALYZER_MODE: import.meta.env.ANALYZER_MODE
  });

  console.log('API Endpoints:', {
    RESUME_GET_ALL: import.meta.env.VITE_API_URL + '/api/resumes/user'
  });
}

// Log CORS errors
export function logCorsError(error) {
  if (error.name === 'AxiosError' && !error.response) {
    console.error('Network/CORS Error:', {
      message: error.message,
      config: {
        url: error.config?.url,
        method: error.config?.method,
        headers: error.config?.headers,
        withCredentials: error.config?.withCredentials
      },
      stack: error.stack
    });
  }
}

// Check if the backend is reachable
export async function checkBackendConnection() {
  try {
    const response = await fetch(import.meta.env.VITE_API_URL + '/');
    console.log('Backend connection check:', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries())
    });
    return true;
  } catch (error) {
    console.error('Backend connection failed:', error);
    return false;
  }
}
