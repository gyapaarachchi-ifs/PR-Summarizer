/**
 * Error Boundary Component
 * Task: T038 - Error handling polish
 * 
 * React Error Boundary for catching and displaying JavaScript errors
 * anywhere in the component tree with graceful fallback UI.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import './ErrorBoundary.css';

// ===== TYPES =====

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorDetails {
  message: string;
  stack?: string;
  componentStack: string;
  timestamp: string;
  userAgent: string;
  url: string;
}

// ===== ERROR BOUNDARY CLASS =====

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state to show fallback UI
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error details
    this.logError(error, errorInfo);

    // Update state with error info
    this.setState({
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private logError = (error: Error, errorInfo: ErrorInfo): void => {
    const errorDetails: ErrorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack || 'No component stack available',
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 React Error Boundary Caught Error');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Error Details:', errorDetails);
      console.groupEnd();
    }

    // In production, send to error reporting service
    if (process.env.NODE_ENV === 'production') {
      this.reportError(errorDetails);
    }
  };

  private reportError = async (errorDetails: ErrorDetails): Promise<void> => {
    try {
      // Example: Send to error reporting service
      // Replace with your actual error reporting endpoint
      await fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'javascript_error',
          details: errorDetails,
        }),
      });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  private handleReload = (): void => {
    window.location.reload();
  };

  private copyErrorDetails = async (): Promise<void> => {
    if (!this.state.error || !this.state.errorInfo) return;

    const errorText = `
Error ID: ${this.state.errorId}
Timestamp: ${new Date().toISOString()}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}

Error Message: ${this.state.error.message}

Stack Trace:
${this.state.error.stack || 'No stack trace available'}

Component Stack:
${this.state.errorInfo.componentStack}
    `.trim();

    try {
      await navigator.clipboard.writeText(errorText);
      // You could show a toast or temporary message here
      console.log('Error details copied to clipboard');
    } catch (err) {
      console.error('Failed to copy error details:', err);
      // Fallback: Select text in a textarea
      const textArea = document.createElement('textarea');
      textArea.value = errorText;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="error-boundary">
          <div className="error-boundary__container">
            <div className="error-boundary__icon">
              💥
            </div>
            
            <h1 className="error-boundary__title">
              Oops! Something went wrong
            </h1>
            
            <p className="error-boundary__message">
              We're sorry, but something unexpected happened. 
              The error has been logged and our team has been notified.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-boundary__details">
                <summary className="error-boundary__details-summary">
                  Error Details (Development Mode)
                </summary>
                <div className="error-boundary__error-content">
                  <div className="error-boundary__error-section">
                    <h3>Error Message:</h3>
                    <pre className="error-boundary__error-text">
                      {this.state.error.message}
                    </pre>
                  </div>
                  
                  {this.state.error.stack && (
                    <div className="error-boundary__error-section">
                      <h3>Stack Trace:</h3>
                      <pre className="error-boundary__error-text">
                        {this.state.error.stack}
                      </pre>
                    </div>
                  )}
                  
                  {this.state.errorInfo && (
                    <div className="error-boundary__error-section">
                      <h3>Component Stack:</h3>
                      <pre className="error-boundary__error-text">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            <div className="error-boundary__actions">
              <button
                className="error-boundary__button error-boundary__button--primary"
                onClick={this.handleRetry}
              >
                <span className="error-boundary__button-icon">🔄</span>
                Try Again
              </button>
              
              <button
                className="error-boundary__button error-boundary__button--secondary"
                onClick={this.handleReload}
              >
                <span className="error-boundary__button-icon">↻</span>
                Reload Page
              </button>

              {process.env.NODE_ENV === 'development' && (
                <button
                  className="error-boundary__button error-boundary__button--tertiary"
                  onClick={this.copyErrorDetails}
                  title="Copy error details to clipboard"
                >
                  <span className="error-boundary__button-icon">📋</span>
                  Copy Details
                </button>
              )}
            </div>

            {this.state.errorId && (
              <div className="error-boundary__error-id">
                <span className="error-boundary__error-id-label">Error ID:</span>
                <code className="error-boundary__error-id-value">
                  {this.state.errorId}
                </code>
              </div>
            )}

            <div className="error-boundary__support">
              <p className="error-boundary__support-text">
                If this problem persists, please contact support with the error ID above.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;