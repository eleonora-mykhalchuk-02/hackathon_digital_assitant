/* Main Chat UI component */

import React, { useState, useRef, useEffect } from 'react';
import type {
  Message as MessageType,
  JudgeEvaluation,
  ConversationMode as ConversationModeType,
} from '../types';
import { MessageRole, WebSocketEventType, ConversationMode } from '../types';
import { wsClient } from '../services/websocket';
import { Message } from './Message';

interface ChatUIProps {
  onEvaluationUpdate: (evaluation: JudgeEvaluation | null) => void;
  onIterationUpdate: (iteration: number | undefined) => void;
}

export const ChatUI: React.FC<ChatUIProps> = ({ onEvaluationUpdate, onIterationUpdate }) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isJudging, setIsJudging] = useState(false);
  const [currentEvaluation, setCurrentEvaluation] = useState<JudgeEvaluation | null>(null);
  const [streamingCriteria, setStreamingCriteria] = useState<JudgeEvaluation | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [lastUserMessage, setLastUserMessage] = useState<string>('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [mode] = useState<ConversationModeType>(ConversationMode.INPUT_CRITIQUE);
  const [inputEvaluation, setInputEvaluation] = useState<JudgeEvaluation | null>(null);
  const [isStopped, setIsStopped] = useState(false); // Track if user pressed stop
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to WebSocket
    wsClient.connect().catch(console.error);

    // Define event handlers
    const handleGenerating = () => {
      setIsLoading(true);
      setCurrentEvaluation(null);
      onEvaluationUpdate(null);
    };

    const handleInputCritique = (data: any) => {
      // Input critique removed for simplified UI
      console.log('Input critique:', data.critique);
    };

    const handleChatbotChunk = (data: any) => {
      if (isStopped) return; // Ignore if stopped
      const chunk = data.chunk;
      setStreamingMessage((prev) => prev + chunk);
    };

    const handleChatbotResponse = (data: any) => {
      const response = data.response;
      const newMessage: MessageType = {
        id: `msg_${Date.now()}`,
        role: MessageRole.ASSISTANT,
        content: response,
        timestamp: new Date().toISOString(),
        metadata: { iteration: data.iteration },
      };
      setMessages((prev) => [...prev, newMessage]);
      setStreamingMessage('');
      setIsLoading(false); // Stop loading indicator after response is shown
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }
      // Update iteration count
      if (data.iteration) {
        onIterationUpdate(data.iteration);
      }
    };

    const handleJudgeEvaluating = () => {
      if (isStopped) return; // Ignore if stopped
      setIsJudging(true);
      setStreamingCriteria({ criteria_scores: [], overall_score: 0, feedback: '', should_regenerate: false, suggestions: [], traffic_light: '⚪' });
    };

    const handleJudgeCriterionResult = (data: any) => {
      if (isStopped) return; // Ignore if stopped
      const criterion = data.criterion;
      setStreamingCriteria((prev) => {
        const updated = prev 
          ? { ...prev, criteria_scores: [...prev.criteria_scores, criterion] }
          : { criteria_scores: [criterion], overall_score: 0, feedback: '', should_regenerate: false, suggestions: [], traffic_light: '⚪' };
        
        // Update the last assistant message with streaming evaluation
        setMessages((prevMessages) => {
          const lastAssistantIndex = prevMessages.length - 1;
          if (lastAssistantIndex >= 0 && prevMessages[lastAssistantIndex].role === MessageRole.ASSISTANT) {
            const updatedMessages = [...prevMessages];
            updatedMessages[lastAssistantIndex] = {
              ...updatedMessages[lastAssistantIndex],
              metadata: {
                ...updatedMessages[lastAssistantIndex].metadata,
                streaming_evaluation: updated
              }
            };
            return updatedMessages;
          }
          return prevMessages;
        });
        
        return updated;
      });
    };

    const handleJudgeResult = (data: any) => {
      if (isStopped) return; // Ignore if stopped
      setIsJudging(false);
      setCurrentEvaluation(data.evaluation);
      setStreamingCriteria(null);
      onEvaluationUpdate(data.evaluation);
      
      // Update the last assistant message with final evaluation
      setMessages((prevMessages) => {
        const lastAssistantIndex = prevMessages.length - 1;
        if (lastAssistantIndex >= 0 && prevMessages[lastAssistantIndex].role === MessageRole.ASSISTANT) {
          const updatedMessages = [...prevMessages];
          updatedMessages[lastAssistantIndex] = {
            ...updatedMessages[lastAssistantIndex],
            metadata: {
              ...updatedMessages[lastAssistantIndex].metadata,
              evaluation: data.evaluation,
              streaming_evaluation: undefined // Clear streaming evaluation
            }
          };
          return updatedMessages;
        }
        return prevMessages;
      });
    };

    const handleFinalResponse = () => {
      setIsLoading(false);
      setIsJudging(false);
    };

    const handleError = (data: any) => {
      setIsLoading(false);
      alert(`Error: ${data.error}`);
    };

    const handleUserInputEvaluation = (data: any) => {
      const criterion = data.criterion;
      const messageId = data.message_id;
      console.log('Received USER_INPUT_EVALUATION:', criterion, 'for message:', messageId);
      
      // Update the specific user message with this criterion
      setMessages((prevMessages) => {
        return prevMessages.map(msg => {
          if (msg.id === messageId) {
            const currentEval = msg.metadata.inputEvaluation || { criteria_scores: [], overall_score: 0, feedback: '', should_regenerate: false, suggestions: [], traffic_light: '⚪' };
            const updated = { ...currentEval, criteria_scores: [...currentEval.criteria_scores, criterion] };
            return { ...msg, metadata: { ...msg.metadata, inputEvaluation: updated } };
          }
          return msg;
        });
      });
      
      // Also update state for the last evaluation
      setInputEvaluation((prev) => {
        const updated = prev 
          ? { ...prev, criteria_scores: [...prev.criteria_scores, criterion] }
          : { criteria_scores: [criterion], overall_score: 0, feedback: '', should_regenerate: false, suggestions: [], traffic_light: '⚪' };
        console.log('Updated inputEvaluation:', updated);
        return updated;
      });
    };

    // Register event handlers
    wsClient.on(WebSocketEventType.CHATBOT_GENERATING, handleGenerating);
    wsClient.on(WebSocketEventType.JUDGE_INPUT_CRITIQUE, handleInputCritique);
    wsClient.on(WebSocketEventType.CHATBOT_CHUNK, handleChatbotChunk);
    wsClient.on(WebSocketEventType.CHATBOT_RESPONSE, handleChatbotResponse);
    wsClient.on(WebSocketEventType.JUDGE_EVALUATING, handleJudgeEvaluating);
    wsClient.on(WebSocketEventType.JUDGE_CRITERION_RESULT, handleJudgeCriterionResult);
    wsClient.on(WebSocketEventType.JUDGE_RESULT, handleJudgeResult);
    wsClient.on(WebSocketEventType.FINAL_RESPONSE, handleFinalResponse);
    wsClient.on(WebSocketEventType.ERROR, handleError);
    wsClient.on(WebSocketEventType.USER_INPUT_EVALUATION, handleUserInputEvaluation);

    // Cleanup function
    return () => {
      wsClient.off(WebSocketEventType.CHATBOT_GENERATING, handleGenerating);
      wsClient.off(WebSocketEventType.JUDGE_INPUT_CRITIQUE, handleInputCritique);
      wsClient.off(WebSocketEventType.CHATBOT_CHUNK, handleChatbotChunk);
      wsClient.off(WebSocketEventType.CHATBOT_RESPONSE, handleChatbotResponse);
      wsClient.off(WebSocketEventType.JUDGE_EVALUATING, handleJudgeEvaluating);
      wsClient.off(WebSocketEventType.JUDGE_CRITERION_RESULT, handleJudgeCriterionResult);
      wsClient.off(WebSocketEventType.JUDGE_RESULT, handleJudgeResult);
      wsClient.off(WebSocketEventType.FINAL_RESPONSE, handleFinalResponse);
      wsClient.off(WebSocketEventType.ERROR, handleError);
      wsClient.off(WebSocketEventType.USER_INPUT_EVALUATION, handleUserInputEvaluation);
      wsClient.disconnect();
    };
  }, [onEvaluationUpdate, onIterationUpdate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || isJudging) return;

    const userMessageContent = inputValue;
    setInputValue('');
    setIsLoading(true);
    setIsStopped(false); // Clear stopped flag

    // Reset evaluation state
    setInputEvaluation({ criteria_scores: [], overall_score: 0, feedback: '', should_regenerate: false, suggestions: [], traffic_light: '⚪' });

    // Add user message immediately with unique ID
    const tempUserId = `msg_${Date.now()}`;
    const userMessage: MessageType = {
      id: tempUserId,
      role: MessageRole.USER,
      content: userMessageContent,
      timestamp: new Date().toISOString(),
      metadata: {},
    };
    setMessages((prev) => [...prev, userMessage]);
    setLastUserMessage(userMessageContent);

    // Send message with message_id - backend will handle evaluation sequentially
    wsClient.send('user_message', {
      message: userMessageContent,
      conversation_id: conversationId,
      mode,
      message_id: tempUserId,
    });
  };

  const handleStop = () => {
    setIsStopped(true);
    setIsLoading(false);
    setIsJudging(false);
    setStreamingMessage('');
  };

  const handleRetry = () => {
    if (!lastUserMessage || isLoading || isJudging) return;
    
    setIsStopped(false); // Clear stopped flag
    
    // Remove last assistant message if exists
    let lastUserMessageId: string | undefined;
    setMessages((prev) => {
      // Find last user message ID
      for (let i = prev.length - 1; i >= 0; i--) {
        if (prev[i].role === MessageRole.USER && prev[i].content === lastUserMessage) {
          lastUserMessageId = prev[i].id;
          break;
        }
      }
      
      // Remove last assistant message
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.role === MessageRole.ASSISTANT) {
        return prev.slice(0, -1);
      }
      return prev;
    });

    // Send retry request with skip_user_evaluation flag
    wsClient.send('user_message', {
      message: lastUserMessage,
      conversation_id: conversationId,
      mode,
      message_id: lastUserMessageId,
      skip_user_evaluation: true, // Skip user evaluation on retry
    });

    setIsLoading(true);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Update user message with input evaluation once it's complete
  useEffect(() => {
    if (inputEvaluation && inputEvaluation.criteria_scores.length > 0) {
      setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        // Update if last message is a user message (could be in progress of evaluation)
        if (lastMsg && lastMsg.role === MessageRole.USER) {
          console.log('Updating user message with evaluation:', inputEvaluation);
          return [
            ...prev.slice(0, -1),
            {
              ...lastMsg,
              metadata: { ...lastMsg.metadata, inputEvaluation }
            }
          ];
        }
        return prev;
      });
    }
  }, [inputEvaluation]);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Digitale Assistent</h1>
          <p style={styles.subtitle}>Altijd beschikbaar om te helpen</p>
        </div>
      </div>

      {/* Messages */}
      <div style={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div style={styles.emptyState}>
            <p>Start een gesprek door een bericht te typen</p>
          </div>
        ) : (
          <>
            {messages.map((message, index) => {
              const isLastAssistant = message.role === MessageRole.ASSISTANT && 
                                     index === messages.length - 1;
              
              // Show streaming criteria for the last assistant message while judging
              const evaluationToShow = isLastAssistant && isJudging && streamingCriteria 
                ? streamingCriteria 
                : (isLastAssistant ? currentEvaluation : null);
              
              return (
                <Message 
                  key={message.id}
                  message={message} 
                  evaluation={evaluationToShow}
                />
              );
            })}
          </>
        )}
        {streamingMessage && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'row',
              alignItems: 'flex-start',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: '#667EEA',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.9rem',
                fontWeight: 600,
                flexShrink: 0,
              }}
            >
              AI
            </div>
            <div style={{ flex: 1, maxWidth: '70%' }}>
              <div
                style={{
                  padding: '1rem 1.25rem',
                  borderRadius: '1rem',
                  backgroundColor: 'white',
                  color: '#1F2937',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                  wordWrap: 'break-word',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {streamingMessage}
                <span style={{ opacity: 0.5, animation: 'blink 1s infinite' }}>▊</span>
              </div>
            </div>
          </div>
        )}
        {isLoading && !streamingMessage && (
          <div style={styles.loadingMessage}>
            <div style={styles.avatar}>AI</div>
            <div>
              <div style={styles.typingIndicator} className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span style={styles.loadingText}>Bezig met antwoord genereren...</span>
            </div>
          </div>
        )}
        {isJudging && (
          <div style={styles.loadingMessage}>
            <div style={styles.avatar}>AI</div>
            <div>
              <div style={styles.typingIndicator} className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span style={styles.loadingText}>Bezig met evalueren van het antwoord...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={styles.inputContainer}>
        <div style={styles.inputWrapper}>
          <textarea
            style={styles.input}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Typ je bericht..."
            disabled={isLoading || isJudging}
            rows={1}
          />
          <div style={styles.buttonGroup}>
            {(isLoading || isJudging) && (
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <button
                  style={styles.stopButton}
                  onClick={handleStop}
                  onMouseEnter={(e) => {
                    const tooltip = e.currentTarget.nextElementSibling as HTMLElement;
                    if (tooltip) tooltip.style.opacity = '1';
                  }}
                  onMouseLeave={(e) => {
                    const tooltip = e.currentTarget.nextElementSibling as HTMLElement;
                    if (tooltip) tooltip.style.opacity = '0';
                  }}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2"/>
                    <rect x="8" y="8" width="8" height="8" rx="1"/>
                  </svg>
                </button>
                <span style={styles.buttonTooltip}>
                  Stop genereren
                  <span style={styles.tooltipArrow} />
                </span>
              </div>
            )}
            {!isLoading && !isJudging && lastUserMessage && (
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <button
                  style={styles.retryButton}
                  onClick={handleRetry}
                  onMouseEnter={(e) => {
                    const tooltip = e.currentTarget.nextElementSibling as HTMLElement;
                    if (tooltip) tooltip.style.opacity = '1';
                  }}
                  onMouseLeave={(e) => {
                    const tooltip = e.currentTarget.nextElementSibling as HTMLElement;
                    if (tooltip) tooltip.style.opacity = '0';
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/>
                  </svg>
                </button>
                <span style={styles.buttonTooltip}>
                  Opnieuw proberen
                  <span style={styles.tooltipArrow} />
                </span>
              </div>
            )}
            <button
              style={styles.sendButton(isLoading || isJudging || !inputValue.trim())}
              onClick={handleSend}
              disabled={isLoading || isJudging || !inputValue.trim()}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
              Verstuur
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, any> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: '#F5F5F5',
  },
  header: {
    padding: '2rem 2rem 1.5rem',
    backgroundColor: 'white',
    borderBottom: '1px solid #E5E5E5',
  },
  title: {
    margin: 0,
    fontSize: '1.75rem',
    fontWeight: 600,
    color: '#1A1A1A',
  },
  subtitle: {
    margin: '0.25rem 0 0 0',
    fontSize: '0.95rem',
    fontWeight: 400,
    color: '#666666',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '2rem',
    maxWidth: '900px',
    width: '100%',
    margin: '0 auto',
  },
  emptyState: {
    textAlign: 'center',
    padding: '4rem 2rem',
    color: '#999999',
    fontSize: '0.95rem',
  },
  loadingMessage: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  avatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: '#667EEA',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.9rem',
    fontWeight: 600,
    flexShrink: 0,
  },
  typingIndicator: {
    display: 'flex',
    gap: '0.3rem',
    padding: '1rem 1.25rem',
    backgroundColor: 'white',
    borderRadius: '1rem',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  loadingText: {
    marginTop: '0.5rem',
    fontSize: '0.85rem',
    color: '#6B7280',
    fontStyle: 'italic',
  },
  inputContainer: {
    padding: '1.5rem 2rem',
    backgroundColor: 'white',
    borderTop: '1px solid #E5E5E5',
    maxWidth: '900px',
    width: '100%',
    margin: '0 auto',
  },
  inputWrapper: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    padding: '0.875rem 1rem',
    border: '1px solid #D1D5DB',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
    fontFamily: 'inherit',
    outline: 'none',
    resize: 'none',
    minHeight: '3rem',
    maxHeight: '8rem',
  },
  buttonGroup: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
  },
  stopButton: {
    padding: '0.75rem',
    backgroundColor: '#6B7280',
    color: 'white',
    border: 'none',
    borderRadius: '0.5rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s',
  },
  retryButton: {
    padding: '0.75rem',
    backgroundColor: '#6B7280',
    color: 'white',
    border: 'none',
    borderRadius: '0.5rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s',
  },
  buttonTooltip: {
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
  },
  tooltipArrow: {
    position: 'absolute',
    top: '100%',
    left: '50%',
    transform: 'translateX(-50%)',
    borderLeft: '6px solid transparent',
    borderRight: '6px solid transparent',
    borderTop: '6px solid #1F2937',
  },
  sendButton: (disabled: boolean): React.CSSProperties => ({
    padding: '0.875rem 1.75rem',
    backgroundColor: disabled ? '#9CA3AF' : '#2563EB',
    color: 'white',
    border: 'none',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
    fontWeight: 500,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'background-color 0.2s',
  }),
};

export default ChatUI;
