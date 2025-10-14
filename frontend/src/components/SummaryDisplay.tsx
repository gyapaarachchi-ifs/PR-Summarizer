/**
 * SummaryDisplay Component  
 * Task: T035 - Create SummaryDisplay component
 * 
 * Component for displaying generated PR summaries with structured sections,
 * copy functionality, export options, and responsive design.
 */

import React, { useState, useCallback, useMemo } from 'react';
import './SummaryDisplay.css';

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

export interface SummaryDisplayProps {
  summary: PRSummary | null;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
  onNewSummary?: () => void;
  showActions?: boolean;
}

interface SummarySection {
  key: keyof PRSummary;
  title: string;
  icon: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

const SUMMARY_SECTIONS: SummarySection[] = [
  {
    key: 'business_context',
    title: 'Business Context',
    icon: '🎯',
    description: 'Purpose and business rationale for this change',
    priority: 'high'
  },
  {
    key: 'code_change_summary',
    title: 'Technical Summary',
    icon: '⚙️',
    description: 'Technical overview of code modifications',
    priority: 'high'
  },
  {
    key: 'business_code_impact',
    title: 'Business Impact',
    icon: '📈',
    description: 'How code changes affect business objectives',
    priority: 'high'
  },
  {
    key: 'suggested_test_cases',
    title: 'Suggested Test Cases',
    icon: '🧪',
    description: 'Recommended testing scenarios and cases',
    priority: 'medium'
  },
  {
    key: 'risk_complexity',
    title: 'Risk Assessment',
    icon: '⚠️',
    description: 'Complexity analysis and potential risks',
    priority: 'medium'
  },
  {
    key: 'reviewer_guidance',
    title: 'Review Guidance',
    icon: '👥',
    description: 'Guidelines and focus areas for code reviewers',
    priority: 'medium'
  }
];

export const SummaryDisplay: React.FC<SummaryDisplayProps> = ({
  summary,
  loading = false,
  error,
  onRetry,
  onNewSummary,
  showActions = true
}) => {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  /**
   * Copy text to clipboard with feedback
   */
  const copyToClipboard = useCallback(async (text: string, sectionKey: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedSection(sectionKey);
      
      // Clear copied status after 2 seconds
      setTimeout(() => {
        setCopiedSection(null);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopiedSection(sectionKey);
      setTimeout(() => setCopiedSection(null), 2000);
    }
  }, []);

  /**
   * Copy entire summary as formatted text
   */
  const copyFullSummary = useCallback(async () => {
    if (!summary) return;

    const formatSummary = () => {
      let formatted = `# PR Summary\n\n`;
      formatted += `**GitHub PR:** ${summary.github_pr_url}\n`;
      if (summary.jira_ticket_id) {
        formatted += `**Jira Ticket:** ${summary.jira_ticket_id}\n`;
      }
      formatted += `**Generated:** ${new Date(summary.created_at).toLocaleDateString()}\n\n`;

      SUMMARY_SECTIONS.forEach(section => {
        const content = summary[section.key];
        formatted += `## ${section.title}\n\n`;
        
        if (Array.isArray(content)) {
          content.forEach((item, index) => {
            formatted += `${index + 1}. ${item}\n`;
          });
        } else {
          formatted += `${content}\n`;
        }
        formatted += '\n';
      });

      return formatted;
    };

    await copyToClipboard(formatSummary(), 'full-summary');
  }, [summary, copyToClipboard]);

  /**
   * Toggle section expansion
   */
  const toggleSection = useCallback((sectionKey: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionKey)) {
        newSet.delete(sectionKey);
      } else {
        newSet.add(sectionKey);
      }
      return newSet;
    });
  }, []);

  /**
   * Format processing time
   */
  const formattedProcessingTime = useMemo(() => {
    if (!summary?.processing_time_ms) return null;
    
    const seconds = summary.processing_time_ms / 1000;
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  }, [summary?.processing_time_ms]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <div className="summary-display summary-display--loading">
        <div className="summary-display__loading">
          <div className="summary-display__spinner" />
          <h3 className="summary-display__loading-title">Generating Summary</h3>
          <p className="summary-display__loading-text">
            Analyzing pull request and generating comprehensive summary...
          </p>
          <div className="summary-display__progress">
            <div className="summary-display__progress-bar" />
          </div>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="summary-display summary-display--error">
        <div className="summary-display__error">
          <div className="summary-display__error-icon">❌</div>
          <h3 className="summary-display__error-title">Summary Generation Failed</h3>
          <p className="summary-display__error-message">{error}</p>
          {onRetry && (
            <div className="summary-display__error-actions">
              <button 
                className="summary-display__button summary-display__button--retry"
                onClick={onRetry}
              >
                <span className="summary-display__button-icon">🔄</span>
                Try Again
              </button>
              {onNewSummary && (
                <button 
                  className="summary-display__button summary-display__button--secondary"
                  onClick={onNewSummary}
                >
                  New Summary
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  /**
   * Render empty state
   */
  if (!summary) {
    return (
      <div className="summary-display summary-display--empty">
        <div className="summary-display__empty">
          <div className="summary-display__empty-icon">📝</div>
          <h3 className="summary-display__empty-title">No Summary Yet</h3>
          <p className="summary-display__empty-text">
            Enter a GitHub PR URL above to generate an AI-powered summary.
          </p>
        </div>
      </div>
    );
  }

  /**
   * Render summary content
   */
  return (
    <div className="summary-display summary-display--loaded">
      {/* Summary Header */}
      <div className="summary-display__header">
        <div className="summary-display__meta">
          <h2 className="summary-display__title">PR Summary</h2>
          <div className="summary-display__info">
            <div className="summary-display__info-item">
              <span className="summary-display__info-label">PR:</span>
              <a 
                href={summary.github_pr_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="summary-display__pr-link"
              >
                {summary.github_pr_url.replace('https://github.com/', '')}
                <span className="summary-display__external-icon">🔗</span>
              </a>
            </div>
            
            {summary.jira_ticket_id && (
              <div className="summary-display__info-item">
                <span className="summary-display__info-label">Jira:</span>
                <span className="summary-display__jira-ticket">
                  {summary.jira_ticket_id}
                </span>
              </div>
            )}
            
            <div className="summary-display__info-item">
              <span className="summary-display__info-label">Generated:</span>
              <time className="summary-display__timestamp">
                {new Date(summary.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </time>
            </div>

            {formattedProcessingTime && (
              <div className="summary-display__info-item">
                <span className="summary-display__info-label">Processing:</span>
                <span className="summary-display__processing-time">
                  {formattedProcessingTime}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Header Actions */}
        {showActions && (
          <div className="summary-display__actions">
            <button
              className="summary-display__button summary-display__button--copy"
              onClick={copyFullSummary}
              title="Copy entire summary"
            >
              <span className="summary-display__button-icon">
                {copiedSection === 'full-summary' ? '✅' : '📋'}
              </span>
              {copiedSection === 'full-summary' ? 'Copied!' : 'Copy All'}
            </button>
            
            {onNewSummary && (
              <button
                className="summary-display__button summary-display__button--new"
                onClick={onNewSummary}
                title="Generate new summary"
              >
                <span className="summary-display__button-icon">➕</span>
                New Summary
              </button>
            )}
          </div>
        )}
      </div>

      {/* Summary Sections */}
      <div className="summary-display__content">
        {SUMMARY_SECTIONS.map((section) => {
          const content = summary[section.key];
          const isExpanded = expandedSections.has(section.key);
          const hasContent = Array.isArray(content) 
            ? content.length > 0 
            : Boolean(content && String(content).trim());

          if (!hasContent) return null;

          return (
            <div 
              key={section.key} 
              className={`summary-display__section summary-display__section--${section.priority}`}
            >
              {/* Section Header */}
              <div className="summary-display__section-header">
                <button
                  className="summary-display__section-toggle"
                  onClick={() => toggleSection(section.key)}
                  aria-expanded={isExpanded}
                  aria-controls={`section-${section.key}`}
                >
                  <span className="summary-display__section-icon">
                    {section.icon}
                  </span>
                  <div className="summary-display__section-title-group">
                    <h3 className="summary-display__section-title">
                      {section.title}
                    </h3>
                    <p className="summary-display__section-description">
                      {section.description}
                    </p>
                  </div>
                  <span className={`summary-display__expand-icon ${
                    isExpanded ? 'summary-display__expand-icon--expanded' : ''
                  }`}>
                    ▼
                  </span>
                </button>

                <button
                  className="summary-display__copy-button"
                  onClick={() => {
                    const text = Array.isArray(content) 
                      ? content.join('\n') 
                      : String(content);
                    copyToClipboard(text, section.key);
                  }}
                  title={`Copy ${section.title}`}
                >
                  {copiedSection === section.key ? '✅' : '📋'}
                </button>
              </div>

              {/* Section Content */}
              <div 
                id={`section-${section.key}`}
                className={`summary-display__section-content ${
                  isExpanded ? 'summary-display__section-content--expanded' : ''
                }`}
              >
                <div className="summary-display__section-body">
                  {Array.isArray(content) ? (
                    <ul className="summary-display__list">
                      {content.map((item, index) => (
                        <li key={index} className="summary-display__list-item">
                          {item}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="summary-display__text">
                      {String(content).split('\n').map((paragraph, index) => (
                        paragraph.trim() && (
                          <p key={index} className="summary-display__paragraph">
                            {paragraph.trim()}
                          </p>
                        )
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Footer */}
      <div className="summary-display__footer">
        <div className="summary-display__status">
          <span className={`summary-display__status-badge summary-display__status-badge--${summary.status}`}>
            {summary.status === 'completed' && '✅'}
            {summary.status === 'pending' && '⏳'}
            {summary.status === 'in_progress' && '⚡'}
            {summary.status === 'failed' && '❌'}
            {summary.status === 'cancelled' && '🚫'}
            {summary.status.replace('_', ' ').toUpperCase()}
          </span>
          <span className="summary-display__summary-id">
            ID: {summary.id}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SummaryDisplay;