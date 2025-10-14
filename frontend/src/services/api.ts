/**
 * API Client Service
 * Task: T036 - Create API client service
 * 
 * Service for communicating with the PR Summarizer backend API
 * with proper error handling, retry logic, and TypeScript types.
 */

// ===== TYPES AND INTERFACES =====

export interface SummaryRequest {
  githubPrUrl: string;
  jiraTicketId?: string;
}

export interface PRSummary {
  id: string;
  request_id?: string;
  github_pr_url: string;
  jira_ticket_id?: string;
  business_context: string;
  code_change_summary: string;
  business_code_impact: string;
  suggested_test_cases: string[];
  risk_complexity: string;
  reviewer_guidance: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  processing_time_ms?: number;
}

export interface APIError {
  error: string;
  message: string;
  timestamp: string;
  correlation_id?: string;
  path?: string;
  method?: string;
  details?: Record<string, any>;
}

export interface ValidationError extends APIError {
  errors: Array<{
    field: string;
    message: string;
    code: string;
    value?: any;
  }>;
}

export interface AsyncTaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  services?: Record<string, string>;
  version?: string;
  error?: string;
}

export interface ServiceMetrics {
  timestamp: string;
  metrics: {
    performance: {
      total_summaries_generated: number;
      average_processing_time_ms: number;
      success_rate: number;
    };
    health: {
      service_initialized: boolean;
      dependencies_count: number;
      uptime_seconds: number;
    };
  };
  status: string;
}

// ===== ERROR CLASSES =====

export class APIClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public errorCode?: string,
    public correlationId?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'APIClientError';
  }
}

export class ValidationAPIError extends APIClientError {
  constructor(
    message: string,
    public validationErrors: ValidationError['errors'],
    correlationId?: string
  ) {
    super(message, 400, 'VALIDATION_ERROR', correlationId);
    this.name = 'ValidationAPIError';
  }
}

export class NetworkError extends APIClientError {
  constructor(message: string, public originalError?: Error) {
    super(message, 0, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends APIClientError {
  constructor(message: string = 'Request timed out') {
    super(message, 0, 'TIMEOUT_ERROR');
    this.name = 'TimeoutError';
  }
}

// ===== CONFIGURATION =====

export interface APIClientConfig {
  baseURL?: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  retryBackoff?: boolean;
  enableLogging?: boolean;
}

const DEFAULT_CONFIG: Required<APIClientConfig> = {
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
  retryBackoff: true,
  enableLogging: process.env.NODE_ENV === 'development',
};

// ===== UTILITY FUNCTIONS =====

const sleep = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

const isRetryableError = (error: APIClientError): boolean => {
  if (!error.statusCode) return true; // Network errors
  return error.statusCode >= 500 || error.statusCode === 429; // Server errors or rate limiting
};

const log = (message: string, data?: any) => {
  if (DEFAULT_CONFIG.enableLogging) {
    console.log(`[APIClient] ${message}`, data || '');
  }
};

// ===== MAIN API CLIENT CLASS =====

export class APIClient {
  private config: Required<APIClientConfig>;
  private abortController: AbortController | null = null;

  constructor(config: APIClientConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    log('API Client initialized', { baseURL: this.config.baseURL });
  }

  /**
   * Update client configuration
   */
  updateConfig(config: Partial<APIClientConfig>): void {
    this.config = { ...this.config, ...config };
    log('Configuration updated', config);
  }

  /**
   * Cancel ongoing requests
   */
  cancelRequests(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
      log('Requests cancelled');
    }
  }

  /**
   * Core HTTP request method with retry logic
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`;
    
    // Create new abort controller for this request
    this.abortController = new AbortController();
    
    const requestOptions: RequestInit = {
      ...options,
      signal: this.abortController.signal,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      },
    };

    log(`${options.method || 'GET'} ${endpoint}`, { 
      attempt: retryCount + 1,
      maxRetries: this.config.retries 
    });

    try {
      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new TimeoutError()), this.config.timeout);
      });

      // Make the request with timeout
      const response = await Promise.race([
        fetch(url, requestOptions),
        timeoutPromise
      ]);

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await this.parseErrorResponse(response);
        throw this.createAPIError(response.status, errorData);
      }

      // Parse successful response
      const data = await response.json();
      log(`${options.method || 'GET'} ${endpoint} - Success`);
      return data;

    } catch (error) {
      // Handle abort
      if (error instanceof Error && error.name === 'AbortError') {
        log(`${options.method || 'GET'} ${endpoint} - Aborted`);
        throw new APIClientError('Request was cancelled', 0, 'CANCELLED');
      }

      // Handle timeout
      if (error instanceof TimeoutError) {
        log(`${options.method || 'GET'} ${endpoint} - Timeout`);
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new NetworkError(
          'Network error - please check your connection',
          error
        );
        log(`${options.method || 'GET'} ${endpoint} - Network Error`, error.message);
        throw networkError;
      }

      // Retry logic for retryable errors
      if (error instanceof APIClientError && 
          retryCount < this.config.retries && 
          isRetryableError(error)) {
        
        const delay = this.config.retryBackoff 
          ? this.config.retryDelay * Math.pow(2, retryCount)
          : this.config.retryDelay;

        log(`${options.method || 'GET'} ${endpoint} - Retrying after ${delay}ms`, {
          error: error.message,
          attempt: retryCount + 1
        });

        await sleep(delay);
        return this.request<T>(endpoint, options, retryCount + 1);
      }

      // Re-throw non-retryable or max-retry-reached errors
      log(`${options.method || 'GET'} ${endpoint} - Failed`, error);
      throw error;
    }
  }

  /**
   * Parse error response from API
   */
  private async parseErrorResponse(response: Response): Promise<APIError | ValidationError> {
    try {
      const errorData = await response.json();
      return errorData;
    } catch {
      // Fallback for non-JSON error responses
      return {
        error: 'HTTP Error',
        message: `HTTP ${response.status} - ${response.statusText}`,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Create appropriate error instance based on response
   */
  private createAPIError(statusCode: number, errorData: APIError | ValidationError): APIClientError {
    if (statusCode === 400 && 'errors' in errorData) {
      return new ValidationAPIError(
        errorData.message,
        errorData.errors,
        errorData.correlation_id
      );
    }

    return new APIClientError(
      errorData.message,
      statusCode,
      errorData.error,
      errorData.correlation_id,
      errorData.details
    );
  }

  // ===== PUBLIC API METHODS =====

  /**
   * Generate PR summary
   */
  async generateSummary(request: SummaryRequest): Promise<PRSummary> {
    const cleanRequest = {
      github_pr_url: request.githubPrUrl.trim(),
      jira_ticket_id: request.jiraTicketId?.trim() || undefined,
    };

    return this.request<PRSummary>('/api/v1/summary/generate', {
      method: 'POST',
      body: JSON.stringify(cleanRequest),
    });
  }

  /**
   * Start asynchronous summary generation
   */
  async generateSummaryAsync(request: SummaryRequest): Promise<AsyncTaskResponse> {
    const cleanRequest = {
      github_pr_url: request.githubPrUrl.trim(),
      jira_ticket_id: request.jiraTicketId?.trim() || undefined,
    };

    return this.request<AsyncTaskResponse>('/api/v1/summary/generate-async', {
      method: 'POST',
      body: JSON.stringify(cleanRequest),
    });
  }

  /**
   * Check service health
   */
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/api/v1/summary/health');
  }

  /**
   * Get service metrics
   */
  async getMetrics(): Promise<ServiceMetrics> {
    return this.request<ServiceMetrics>('/api/v1/summary/metrics');
  }

  /**
   * Basic health check (minimal endpoint)
   */
  async ping(): Promise<{ status: string; service: string; timestamp: string }> {
    return this.request('/health');
  }
}

// ===== SINGLETON INSTANCE =====

let apiClientInstance: APIClient | null = null;

/**
 * Get or create API client singleton
 */
export const getAPIClient = (config?: APIClientConfig): APIClient => {
  if (!apiClientInstance) {
    apiClientInstance = new APIClient(config);
  } else if (config) {
    apiClientInstance.updateConfig(config);
  }
  return apiClientInstance;
};

/**
 * Reset API client singleton (useful for testing)
 */
export const resetAPIClient = (): void => {
  if (apiClientInstance) {
    apiClientInstance.cancelRequests();
  }
  apiClientInstance = null;
};

// ===== CONVENIENCE FUNCTIONS =====

/**
 * Quick summary generation with default client
 */
export const generateSummary = async (request: SummaryRequest): Promise<PRSummary> => {
  const client = getAPIClient();
  return client.generateSummary(request);
};

/**
 * Quick health check with default client
 */
export const checkHealth = async (): Promise<HealthStatus> => {
  const client = getAPIClient();
  return client.getHealth();
};

/**
 * Quick service metrics with default client
 */
export const getServiceMetrics = async (): Promise<ServiceMetrics> => {
  const client = getAPIClient();
  return client.getMetrics();
};

// ===== REACT HOOKS (BONUS) =====

/**
 * React hook for API client (if used in React context)
 */
export const useAPIClient = (config?: APIClientConfig): APIClient => {
  return getAPIClient(config);
};

// ===== EXPORTS =====

export default APIClient;