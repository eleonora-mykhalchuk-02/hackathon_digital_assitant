/* Judge Panel component with traffic lights */

import React from 'react';
import type { JudgeEvaluation } from '../types';
import { TrafficLight } from './TrafficLight';

interface JudgePanelProps {
  evaluation: JudgeEvaluation | null;
  isLoading?: boolean;
  iteration?: number;
}

export const JudgePanel: React.FC<JudgePanelProps> = ({ evaluation, isLoading, iteration }) => {
  if (isLoading) {
    return (
      <div style={styles.panel}>
        <h3 style={styles.title}>Judge Evaluation</h3>
        <div style={styles.loading}>Evaluating...</div>
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div style={styles.panel}>
        <h3 style={styles.title}>Judge Evaluation</h3>
        <div style={styles.empty}>No evaluation yet. Send a message to get started.</div>
      </div>
    );
  }

  return (
    <div style={styles.panel}>
      <h3 style={styles.title}>Judge Evaluation</h3>

      {/* Overall Score */}
      <div style={styles.overallScore}>
        <div style={styles.scoreNumber}>{evaluation.overall_score.toFixed(1)}</div>
        <TrafficLight score={evaluation.overall_score} size="large" />
        {iteration && iteration > 1 && (
          <div style={styles.iterationBadge}>
            ✨ Refined {iteration - 1} time{iteration > 2 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Criteria Breakdown */}
      <div style={styles.section}>
        <h4 style={styles.sectionTitle}>Criteria Breakdown</h4>
        <div style={styles.criteriaList}>
          {evaluation.criteria_scores.map((criterion) => (
            <div key={criterion.name} style={styles.criterionCard}>
              <div style={styles.criterionHeader}>
                <span style={styles.criterionName}>
                  {criterion.name.charAt(0).toUpperCase() + criterion.name.slice(1)}
                </span>
                <div style={styles.criterionScore}>
                  <span style={styles.scoreValue}>{criterion.score.toFixed(0)}</span>
                  <TrafficLight
                    score={criterion.score}
                    greenThreshold={criterion.threshold}
                    orangeThreshold={criterion.threshold * 0.7}
                    size="small"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  panel: {
    height: '100%',
    overflowY: 'auto',
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
    borderLeft: '1px solid #dee2e6',
  },
  title: {
    margin: '0 0 1.5rem 0',
    fontSize: '1.5rem',
    fontWeight: 600,
    color: '#333',
  },
  loading: {
    textAlign: 'center',
    padding: '2rem',
    color: '#6c757d',
  },
  empty: {
    textAlign: 'center',
    padding: '2rem',
    color: '#6c757d',
    fontStyle: 'italic',
  },
  overallScore: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem',
    padding: '1.5rem',
    backgroundColor: 'white',
    borderRadius: '0.75rem',
    marginBottom: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  iterationBadge: {
    fontSize: '0.85rem',
    padding: '0.4rem 0.8rem',
    backgroundColor: '#e7f3ff',
    color: '#0066cc',
    borderRadius: '1rem',
    fontWeight: 500,
  },
  scoreNumber: {
    fontSize: '3rem',
    fontWeight: 700,
    color: '#333',
  },
  section: {
    marginBottom: '1.5rem',
  },
  sectionTitle: {
    margin: '0 0 0.75rem 0',
    fontSize: '1.1rem',
    fontWeight: 600,
    color: '#495057',
  },
  feedback: {
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '0.5rem',
    lineHeight: 1.6,
    color: '#333',
  },
  criteriaList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  criterionCard: {
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '0.5rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  criterionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  criterionName: {
    fontWeight: 600,
    color: '#333',
  },
  criterionScore: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  scoreValue: {
    fontWeight: 600,
    fontSize: '1.1rem',
    color: '#495057',
  },
  criterionFeedback: {
    fontSize: '0.9rem',
    color: '#6c757d',
    marginTop: '0.5rem',
  },
  suggestionsList: {
    margin: 0,
    padding: '0 0 0 1.5rem',
    backgroundColor: 'white',
    borderRadius: '0.5rem',
    paddingTop: '1rem',
    paddingBottom: '1rem',
  },
  suggestion: {
    marginBottom: '0.5rem',
    color: '#333',
    lineHeight: 1.5,
  },
};
