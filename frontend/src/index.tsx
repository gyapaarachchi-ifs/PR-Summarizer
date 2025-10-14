/**
 * React App Entry Point
 * Task: T038 - Error handling polish (React setup)
 * 
 * Application entry point with error boundary and React 18 setup.
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import './index.css';

// ===== GLOBAL ERROR HANDLER =====
const handleGlobalError = (event: ErrorEvent): void => {
  console.error('Global error:', event.error);
  // In production, you might want to send this to an error reporting service
};

const handleUnhandledRejection = (event: PromiseRejectionEvent): void => {
  console.error('Unhandled promise rejection:', event.reason);
  // In production, you might want to send this to an error reporting service
};

// Set up global error handlers
window.addEventListener('error', handleGlobalError);
window.addEventListener('unhandledrejection', handleUnhandledRejection);

// ===== RENDER APPLICATION =====
const container = document.getElementById('root');
if (!container) {
  throw new Error('Root container not found. Make sure you have a div with id="root" in your HTML.');
}

const root = createRoot(container);

root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);