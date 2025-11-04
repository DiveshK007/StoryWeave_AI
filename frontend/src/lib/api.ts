import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { addBreadcrumb, captureException, setTag, trackAPICall } from './sentry';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens and Sentry tracking
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add breadcrumb for API request
    addBreadcrumb(
      `API Request: ${config.method?.toUpperCase()} ${config.url}`,
      'api',
      'info',
      {
        method: config.method,
        url: config.url,
        baseURL: config.baseURL,
      }
    );

    return config;
  },
  (error) => {
    captureException(error as Error, {
      error_type: 'api_request_error',
      phase: 'request_interceptor',
    });
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and Sentry tracking
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Add breadcrumb for successful response
    addBreadcrumb(
      `API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`,
      'api',
      'info',
      {
        status: response.status,
        statusText: response.statusText,
      }
    );

    return response;
  },
  (error: AxiosError) => {
    const status = error.response?.status;
    const statusText = error.response?.statusText;
    const url = error.config?.url;

    // Add breadcrumb for failed request
    addBreadcrumb(
      `API Error: ${error.config?.method?.toUpperCase()} ${url}`,
      'api',
      'error',
      {
        status,
        statusText,
        error: error.message,
      }
    );

    // Tag error by status code
    if (status) {
      setTag('http_status_code', status.toString());
      setTag('error_type', 'api_error');
    }

    // Handle specific error cases
    if (status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    } else if (status === 429) {
      // Rate limiting
      captureException(error as Error, {
        error_type: 'rate_limit',
        endpoint: url,
        status_code: status,
      });
    } else if (status && status >= 500) {
      // Server errors - always capture
      captureException(error as Error, {
        error_type: 'server_error',
        endpoint: url,
        status_code: status,
        response_data: error.response?.data,
      });
    } else if (status && status >= 400) {
      // Client errors - capture with warning level
      captureException(error as Error, {
        error_type: 'client_error',
        endpoint: url,
        status_code: status,
      });
    }

    return Promise.reject(error);
  }
);

// Wrapper function to track API calls with Sentry
export async function apiCall<T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> {
  return trackAPICall(async () => {
    let response: AxiosResponse<T>;
    
    switch (method) {
      case 'GET':
        response = await api.get<T>(url, config);
        break;
      case 'POST':
        response = await api.post<T>(url, data, config);
        break;
      case 'PUT':
        response = await api.put<T>(url, data, config);
        break;
      case 'PATCH':
        response = await api.patch<T>(url, data, config);
        break;
      case 'DELETE':
        response = await api.delete<T>(url, config);
        break;
      default:
        throw new Error(`Unsupported HTTP method: ${method}`);
    }
    
    return response.data;
  }, url, method);
}

export default api;

