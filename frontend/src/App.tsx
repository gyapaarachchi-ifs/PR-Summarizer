/**
 * Main App Component
 * Task: T037 - Create main App component
 * 
 * Root component for the PR Summarizer frontend application
 * integrating InputForm, SummaryDisplay, and API client.
 */

import React, { useState, useCallback, useEffect } from 'react';
import InputForm, { FormData } from './components/InputForm';
import SummaryDisplay, { PRSummary } from './components/SummaryDisplay';
import { 
  getAPIClient, 
  APIClientError, 
  ValidationAPIError, 
  NetworkError, 
  TimeoutError 
} from './services/api';
import './App.css';

// ===== TYPES =====

interface AppState {
  summary: PRSummary | null;
  loading: boolean;
  error: string | null;
  lastRequest: FormData | null;
}

type LoadingState = 
  | 'idle' 
  | 'validating' 
  | 'generating' 
  | 'completing';

// ===== MAIN APP COMPONENT =====

const App: React.FC = () => {
  // ===== STATE =====
  const [appState, setAppState] = useState<AppState>({
    summary: null,
    loading: false,
    error: null,
    lastRequest: null,
  });

  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [healthStatus, setHealthStatus] = useState<'unknown' | 'healthy' | 'unhealthy'>('unknown');

  // ===== API CLIENT =====
  const apiClient = getAPIClient();

  // ===== HEALTH CHECK =====
  const checkAPIHealth = useCallback(async () => {
    try {
      await apiClient.ping();
      setHealthStatus('healthy');
    } catch (error) {
      console.warn('API health check failed:', error);
      setHealthStatus('unhealthy');
    }
  }, [apiClient]);

  // Check API health on mount
  useEffect(() => {
    checkAPIHealth();
    
    // Set up periodic health checks
    const healthCheckInterval = setInterval(checkAPIHealth, 60000); // Every minute
    
    return () => {
      clearInterval(healthCheckInterval);
    };
  }, [checkAPIHealth]);

  // ===== ERROR HANDLING =====
  const getErrorMessage = useCallback((error: Error): string => {
    if (error instanceof ValidationAPIError) {
      const fieldErrors = error.validationErrors
        .map(e => `${e.field}: ${e.message}`)
        .join(', ');
      return `Validation Error: ${fieldErrors}`;
    }

    if (error instanceof NetworkError) {
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    }

    if (error instanceof TimeoutError) {
      return 'The request timed out. The server may be busy. Please try again.';
    }

    if (error instanceof APIClientError) {
      switch (error.statusCode) {
        case 400:
          return `Invalid request: ${error.message}`;
        case 401:
          return 'Authentication required. Please refresh the page and try again.';
        case 403:
          return 'Access denied. You may not have permission to perform this action.';
        case 404:
          return 'Service not found. The API may be temporarily unavailable.';
        case 429:
          return 'Too many requests. Please wait a moment before trying again.';
        case 500:
          return 'Internal server error. Please try again later.';
        case 502:
        case 503:
        case 504:
          return 'Service temporarily unavailable. Please try again in a few moments.';
        default:
          return `Server error (${error.statusCode}): ${error.message}`;
      }
    }

    // Generic error fallback
    return error.message || 'An unexpected error occurred. Please try again.';
  }, []);

  // ===== FORM SUBMISSION =====
  const handleSummaryRequest = useCallback(async (formData: FormData): Promise<void> => {
    // Reset previous state
    setAppState(prev => ({
      ...prev,
      loading: true,
      error: null,
      lastRequest: formData,
    }));

    setLoadingState('validating');

    try {
      // Prepare request data
      const request = {
        githubPrUrl: formData.githubPrUrl,
        jiraTicketId: formData.jiraTicketId,
      };

      setLoadingState('generating');

      // Generate summary
      const summary = await apiClient.generateSummary(request);

      setLoadingState('completing');

      // Update state with success
      setAppState(prev => ({
        ...prev,
        summary,
        loading: false,
        error: null,
      }));

      setLoadingState('idle');

    } catch (error) {
      console.error('Summary generation failed:', error);

      // Update state with error
      const errorMessage = getErrorMessage(error as Error);
      setAppState(prev => ({
        ...prev,
        summary: null,
        loading: false,
        error: errorMessage,
      }));

      setLoadingState('idle');

      // Re-throw to let InputForm handle the error display
      throw error;
    }
  }, [apiClient, getErrorMessage]);

  // ===== RETRY FUNCTIONALITY =====
  const handleRetry = useCallback(async (): Promise<void> => {
    if (appState.lastRequest) {
      await handleSummaryRequest(appState.lastRequest);
    }
  }, [appState.lastRequest, handleSummaryRequest]);

  // ===== NEW SUMMARY =====
  const handleNewSummary = useCallback((): void => {
    setAppState({
      summary: null,
      loading: false,
      error: null,
      lastRequest: null,
    });
    setLoadingState('idle');
  }, []);

  // ===== LOADING MESSAGES =====
  const getLoadingMessage = useCallback((): string => {
    switch (loadingState) {
      case 'validating':
        return 'Validating request...';
      case 'generating':
        return 'Analyzing PR and generating summary...';
      case 'completing':
        return 'Finalizing summary...';
      default:
        return 'Processing...';
    }
  }, [loadingState]);

  // ===== RENDER =====
  return (
    <div className="app">
      {/* Header */}
      <header className="app__header">
        <div className="app__header-content">
          <h1 className="app__title">
            <span className="app__title-icon">🤖</span>
            PR Summarizer
          </h1>
          <p className="app__subtitle">
            AI-powered pull request analysis and summarization
          </p>
          
          {/* Health Status Indicator */}
          <div className={`app__health-status app__health-status--${healthStatus}`}>
            <span className="app__health-icon">
              {healthStatus === 'healthy' && '✅'}
              {healthStatus === 'unhealthy' && '❌'}
              {healthStatus === 'unknown' && '⏳'}
            </span>
            <span className="app__health-text">
              {healthStatus === 'healthy' && 'Service Online'}
              {healthStatus === 'unhealthy' && 'Service Offline'}
              {healthStatus === 'unknown' && 'Checking Status'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="app__main">
        <div className="app__container">
          {/* Input Form Section */}
          <section className="app__section app__section--input">
            <InputForm
              onSubmit={handleSummaryRequest}
              loading={appState.loading}
              disabled={healthStatus === 'unhealthy'}
              initialData={appState.lastRequest || undefined}
            />
            
            {/* Loading Status */}
            {appState.loading && (
              <div className="app__loading-status">
                <div className="app__loading-message">
                  {getLoadingMessage()}
                </div>
                <div className="app__loading-progress">
                  <div className="app__loading-bar">
                    <div className="app__loading-fill"></div>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Summary Display Section */}
          <section className="app__section app__section--summary">
            <SummaryDisplay
              summary={appState.summary}
              loading={appState.loading}
              error={appState.error || undefined}
              onRetry={handleRetry}
              onNewSummary={handleNewSummary}
              showActions={true}
            />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="app__footer">
        <div className="app__footer-content">
          <p className="app__footer-text">
            Powered by AI • Built with React & FastAPI
          </p>
          
          {/* Service Status Links */}
          <div className="app__footer-links">
            {healthStatus === 'healthy' && (
              <button
                className="app__footer-link"
                onClick={() => window.open(`${apiClient['config']?.baseURL}/docs`, '_blank')}
                title="View API Documentation"
              >
                📋 API Docs
              </button>
            )}
            
            <button
              className="app__footer-link"
              onClick={checkAPIHealth}
              title="Check Service Health"
            >
              🔄 Check Status
            </button>
          </div>
        </div>
      </footer>

      {/* Global Error Boundary Fallback */}
      {healthStatus === 'unhealthy' && !appState.loading && (
        <div className="app__service-error">
          <div className="app__service-error-content">
            <h2 className="app__service-error-title">
              Service Temporarily Unavailable
            </h2>
            <p className="app__service-error-message">
              We're having trouble connecting to our servers. 
              Please check your internet connection and try again.
            </p>
            <div className="app__service-error-actions">
              <button
                className="app__service-error-button"
                onClick={checkAPIHealth}
              >
                <span className="app__service-error-button-icon">🔄</span>
                Retry Connection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;