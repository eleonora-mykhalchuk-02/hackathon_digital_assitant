/* Individual message component with avatar and traffic lights */

import React, { useState } from 'react';
import type { Message as MessageType, JudgeEvaluation, CriterionScore } from '../types';
import { MessageRole } from '../types';

interface MessageProps {
  message: MessageType;
  evaluation?: JudgeEvaluation | null;
}

export const Message: React.FC<MessageProps> = ({ message, evaluation }) => {
  const isUser = message.role === MessageRole.USER;
  const [selectedCriterion, setSelectedCriterion] = useState<CriterionScore | null>(null);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' });
  };

  const getTrafficLightColor = (score: number) => {
    if (score >= 70) return '🟢';
    if (score >= 40) return '🟠';
    return '🔴';
  };

  // For user messages, show input evaluation from metadata
  // For assistant messages, show evaluation from metadata (streaming or final)
  const trafficLights = isUser 
    ? (message.metadata?.inputEvaluation?.criteria_scores || null)
    : (message.metadata?.streaming_evaluation?.criteria_scores || message.metadata?.evaluation?.criteria_scores || null);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        gap: '1rem',
        marginBottom: '1.5rem',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: isUser ? '#10B981' : '#667EEA',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.9rem',
          fontWeight: 600,
          flexShrink: 0,
        }}
      >
        {isUser ? 'U' : 'AI'}
      </div>

      {/* Message content */}
      <div style={{ flex: 1, maxWidth: '70%' }}>
        <div
          style={{
            padding: '1rem 1.25rem',
            borderRadius: '1rem',
            backgroundColor: isUser ? '#2563EB' : 'white',
            color: isUser ? 'white' : '#1F2937',
            boxShadow: isUser ? 'none' : '0 1px 2px rgba(0,0,0,0.05)',
            wordWrap: 'break-word',
            whiteSpace: 'pre-wrap',
          }}
        >
          {message.content}
        </div>

        {/* Timestamp and traffic lights */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            marginTop: '0.5rem',
            fontSize: '0.85rem',
            color: '#6B7280',
            flexDirection: isUser ? 'row-reverse' : 'row',
          }}
        >
          <span>{formatTime(message.timestamp)}</span>
          {trafficLights && trafficLights.length > 0 && (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {trafficLights.map((criterion) => (
                <div
                  key={criterion.name}
                  style={{
                    position: 'relative',
                    display: 'inline-block',
                  }}
                >
                  <span
                    onClick={() => setSelectedCriterion(criterion)}
                    style={{
                      fontSize: '1.5rem',
                      cursor: 'pointer',
                      transition: 'transform 0.15s ease',
                      display: 'inline-block',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'scale(1.3)';
                      const tooltip = e.currentTarget.nextElementSibling as HTMLElement;
                      if (tooltip) tooltip.style.opacity = '1';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                      const tooltip = e.currentTarget.nextElementSibling as HTMLElement;
                      if (tooltip) tooltip.style.opacity = '0';
                    }}
                  >
                    {getTrafficLightColor(criterion.score)}
                  </span>
                  <span
                    style={{
                      position: 'absolute',
                      bottom: '100%',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      backgroundColor: '#1F2937',
                      color: 'white',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                      marginBottom: '0.5rem',
                      opacity: 0,
                      pointerEvents: 'none',
                      transition: 'opacity 0.1s ease',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      zIndex: 10,
                    }}
                  >
                    {criterion.name}
                    <span
                      style={{
                        position: 'absolute',
                        top: '100%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        borderLeft: '6px solid transparent',
                        borderRight: '6px solid transparent',
                        borderTop: '6px solid #1F2937',
                      }}
                    />
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Criterion details modal/popup */}
        {selectedCriterion && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
            onClick={() => setSelectedCriterion(null)}
          >
            <div
              style={{
                backgroundColor: 'white',
                borderRadius: '1rem',
                padding: '2rem',
                maxWidth: '500px',
                width: '90%',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                <span style={{ fontSize: '2rem' }}>
                  {getTrafficLightColor(selectedCriterion.score)}
                </span>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#1F2937' }}>
                    {selectedCriterion.name}
                  </h3>
                  <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem', color: '#6B7280' }}>
                    Score: {selectedCriterion.score}/100 • Weight: {selectedCriterion.weight} • 
                    Threshold: {selectedCriterion.threshold}
                  </p>
                </div>
              </div>
              
              <div style={{ marginTop: '1.5rem' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: '#374151', fontWeight: 600 }}>
                  Evaluatie redenering:
                </h4>
                <p style={{ margin: 0, fontSize: '0.9rem', color: '#4B5563', lineHeight: '1.6' }}>
                  {selectedCriterion.feedback || 'Geen feedback beschikbaar.'}
                </p>
              </div>

              <div
                style={{
                  marginTop: '1.5rem',
                  display: 'flex',
                  justifyContent: 'flex-end',
                }}
              >
                <button
                  onClick={() => setSelectedCriterion(null)}
                  style={{
                    padding: '0.5rem 1.5rem',
                    backgroundColor: '#2563EB',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.5rem',
                    fontSize: '0.9rem',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  Sluiten
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
