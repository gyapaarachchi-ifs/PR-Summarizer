/**
 * InputForm Component
 * Task: T034 - Create React InputForm component
 * 
 * Form component for collecting GitHub PR URL and optional Jira ticket ID
 * with validation, loading states, and error handling.
 */

import React, { useState, useCallback } from 'react';
import './InputForm.css';

export interface FormData {
  githubPrUrl: string;
  jiraTicketId?: string;
}

export interface InputFormProps {
  onSubmit: (formData: FormData) => Promise<void>;
  loading?: boolean;
  disabled?: boolean;
  initialData?: Partial<FormData>;
}

interface ValidationErrors {
  githubPrUrl?: string;
  jiraTicketId?: string;
  general?: string;
}

const GITHUB_PR_URL_PATTERN = /^https:\/\/github\.com\/[^\/]+\/[^\/]+\/pull\/\d+$/;
const JIRA_TICKET_PATTERN = /^[A-Z]{1,10}-\d+$/i;

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  loading = false,
  disabled = false,
  initialData = {}
}) => {
  // Form state
  const [formData, setFormData] = useState<FormData>({
    githubPrUrl: initialData.githubPrUrl || '',
    jiraTicketId: initialData.jiraTicketId || ''
  });

  // Validation and UI state
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Validate individual field
   */
  const validateField = useCallback((name: keyof FormData, value: string): string | undefined => {
    switch (name) {
      case 'githubPrUrl':
        if (!value.trim()) {
          return 'GitHub PR URL is required';
        }
        if (!GITHUB_PR_URL_PATTERN.test(value.trim())) {
          return 'Please enter a valid GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)';
        }
        return undefined;

      case 'jiraTicketId':
        if (value.trim() && !JIRA_TICKET_PATTERN.test(value.trim())) {
          return 'Please enter a valid Jira ticket ID (e.g., PROJ-123)';
        }
        return undefined;

      default:
        return undefined;
    }
  }, []);

  /**
   * Validate entire form
   */
  const validateForm = useCallback((data: FormData): ValidationErrors => {
    const newErrors: ValidationErrors = {};

    const githubError = validateField('githubPrUrl', data.githubPrUrl);
    if (githubError) {
      newErrors.githubPrUrl = githubError;
    }

    const jiraError = validateField('jiraTicketId', data.jiraTicketId || '');
    if (jiraError) {
      newErrors.jiraTicketId = jiraError;
    }

    return newErrors;
  }, [validateField]);

  /**
   * Handle input field changes
   */
  const handleInputChange = useCallback((
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = event.target;
    const fieldName = name as keyof FormData;

    // Update form data
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));

    // Clear previous error for this field
    if (errors[fieldName]) {
      setErrors(prev => ({
        ...prev,
        [fieldName]: undefined
      }));
    }

    // Real-time validation for touched fields
    if (touched[fieldName]) {
      const fieldError = validateField(fieldName, value);
      if (fieldError) {
        setErrors(prev => ({
          ...prev,
          [fieldName]: fieldError
        }));
      }
    }
  }, [errors, touched, validateField]);

  /**
   * Handle input field blur (mark as touched)
   */
  const handleInputBlur = useCallback((
    event: React.FocusEvent<HTMLInputElement>
  ) => {
    const { name, value } = event.target;
    const fieldName = name as keyof FormData;

    // Mark field as touched
    setTouched(prev => ({
      ...prev,
      [fieldName]: true
    }));

    // Validate field
    const fieldError = validateField(fieldName, value);
    if (fieldError) {
      setErrors(prev => ({
        ...prev,
        [fieldName]: fieldError
      }));
    }
  }, [validateField]);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    // Prevent double submission
    if (isSubmitting || loading || disabled) {
      return;
    }

    // Mark all fields as touched
    setTouched({
      githubPrUrl: true,
      jiraTicketId: true
    });

    // Validate form
    const validationErrors = validateForm(formData);
    setErrors(validationErrors);

    // Stop if there are validation errors
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    // Submit form
    setIsSubmitting(true);
    setErrors({});

    try {
      // Prepare clean data
      const cleanData: FormData = {
        githubPrUrl: formData.githubPrUrl.trim(),
        jiraTicketId: formData.jiraTicketId?.trim() || undefined
      };

      await onSubmit(cleanData);
      
      // Reset form on successful submission
      setFormData({
        githubPrUrl: '',
        jiraTicketId: ''
      });
      setTouched({});
      setErrors({});

    } catch (error) {
      // Handle submission errors
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'An unexpected error occurred. Please try again.';
      
      setErrors({
        general: errorMessage
      });
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, isSubmitting, loading, disabled, validateForm, onSubmit]);

  /**
   * Check if form is valid
   */
  const isFormValid = Object.keys(validateForm(formData)).length === 0;
  const canSubmit = isFormValid && !isSubmitting && !loading && !disabled;

  return (
    <div className="input-form">
      <div className="input-form__header">
        <h2 className="input-form__title">Generate PR Summary</h2>
        <p className="input-form__description">
          Enter a GitHub pull request URL to generate an AI-powered summary. 
          Optionally include a Jira ticket ID for enhanced context.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="input-form__form" noValidate>
        {/* General Error */}
        {errors.general && (
          <div className="input-form__error input-form__error--general">
            <span className="input-form__error-icon">⚠️</span>
            <span className="input-form__error-message">{errors.general}</span>
          </div>
        )}

        {/* GitHub PR URL Field */}
        <div className="input-form__field">
          <label 
            htmlFor="githubPrUrl" 
            className="input-form__label"
          >
            GitHub PR URL *
          </label>
          <input
            type="url"
            id="githubPrUrl"
            name="githubPrUrl"
            value={formData.githubPrUrl}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            placeholder="https://github.com/owner/repo/pull/123"
            className={`input-form__input ${
              errors.githubPrUrl ? 'input-form__input--error' : ''
            } ${
              touched.githubPrUrl && !errors.githubPrUrl ? 'input-form__input--valid' : ''
            }`}
            disabled={loading || disabled}
            required
            aria-describedby={errors.githubPrUrl ? 'githubPrUrl-error' : undefined}
            aria-invalid={!!errors.githubPrUrl}
          />
          {errors.githubPrUrl && (
            <div 
              id="githubPrUrl-error" 
              className="input-form__error"
              role="alert"
            >
              <span className="input-form__error-icon">❌</span>
              <span className="input-form__error-message">{errors.githubPrUrl}</span>
            </div>
          )}
          <div className="input-form__help">
            Example: https://github.com/microsoft/vscode/pull/123456
          </div>
        </div>

        {/* Jira Ticket ID Field */}
        <div className="input-form__field">
          <label 
            htmlFor="jiraTicketId" 
            className="input-form__label"
          >
            Jira Ticket ID (Optional)
          </label>
          <input
            type="text"
            id="jiraTicketId"
            name="jiraTicketId"
            value={formData.jiraTicketId}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            placeholder="PROJ-123"
            className={`input-form__input ${
              errors.jiraTicketId ? 'input-form__input--error' : ''
            } ${
              touched.jiraTicketId && !errors.jiraTicketId && formData.jiraTicketId 
                ? 'input-form__input--valid' : ''
            }`}
            disabled={loading || disabled}
            aria-describedby={errors.jiraTicketId ? 'jiraTicketId-error' : undefined}
            aria-invalid={!!errors.jiraTicketId}
          />
          {errors.jiraTicketId && (
            <div 
              id="jiraTicketId-error" 
              className="input-form__error"
              role="alert"
            >
              <span className="input-form__error-icon">❌</span>
              <span className="input-form__error-message">{errors.jiraTicketId}</span>
            </div>
          )}
          <div className="input-form__help">
            Example: PROJ-123, TASK-456, or leave empty if not applicable
          </div>
        </div>

        {/* Submit Button */}
        <div className="input-form__actions">
          <button
            type="submit"
            className={`input-form__submit ${
              canSubmit ? 'input-form__submit--enabled' : 'input-form__submit--disabled'
            }`}
            disabled={!canSubmit}
            aria-label={
              isSubmitting || loading 
                ? 'Generating summary...' 
                : 'Generate PR summary'
            }
          >
            {isSubmitting || loading ? (
              <>
                <span className="input-form__spinner" aria-hidden="true">
                  ⏳
                </span>
                <span>Generating Summary...</span>
              </>
            ) : (
              <>
                <span className="input-form__submit-icon" aria-hidden="true">
                  ✨
                </span>
                <span>Generate Summary</span>
              </>
            )}
          </button>
        </div>

        {/* Form Status */}
        {(loading || isSubmitting) && (
          <div className="input-form__status" aria-live="polite">
            <div className="input-form__status-text">
              Analyzing pull request and generating comprehensive summary...
            </div>
            <div className="input-form__progress-bar">
              <div className="input-form__progress-fill"></div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default InputForm;