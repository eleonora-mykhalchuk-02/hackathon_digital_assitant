/* TypeScript types for the application */

export const MessageRole = {
  USER: "user",
  ASSISTANT: "assistant",
  SYSTEM: "system"
} as const;

export type MessageRole = typeof MessageRole[keyof typeof MessageRole];

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface CriterionScore {
  name: string;
  score: number;
  weight: number;
  threshold: number;
  passed: boolean;
  feedback?: string;
}

export interface JudgeEvaluation {
  overall_score: number;
  criteria_scores: CriterionScore[];
  feedback: string;
  should_regenerate: boolean;
  suggestions: string[];
  traffic_light: string;
}

export const ConversationMode = {
  SIMPLE: "simple",
  FEEDBACK: "feedback",
  INPUT_CRITIQUE: "input_critique"
} as const;

export type ConversationMode = typeof ConversationMode[keyof typeof ConversationMode];

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  mode?: ConversationMode;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  evaluation: JudgeEvaluation;
  iteration: number;
  history?: Message[];
}

export const WebSocketEventType = {
  USER_MESSAGE: "user_message",
  USER_INPUT_EVALUATION: "user_input_evaluation",
  JUDGE_INPUT_CRITIQUE: "judge_input_critique",
  CHATBOT_GENERATING: "chatbot_generating",
  CHATBOT_CHUNK: "chatbot_chunk",
  CHATBOT_RESPONSE: "chatbot_response",
  JUDGE_EVALUATING: "judge_evaluating",
  JUDGE_CRITERION_RESULT: "judge_criterion_result",
  JUDGE_RESULT: "judge_result",
  CHATBOT_REFINING: "chatbot_refining",
  FINAL_RESPONSE: "final_response",
  ERROR: "error"
} as const;

export type WebSocketEventType = typeof WebSocketEventType[keyof typeof WebSocketEventType];

export interface WebSocketEvent {
  event: WebSocketEventType;
  data: Record<string, any>;
  timestamp: string;
}

export interface Criterion {
  name: string;
  description: string;
  weight: number;
  enabled: boolean;
  threshold: number;
  evaluation_prompt?: string;
}

export interface CriteriaConfig {
  profiles: Record<string, {
    overall_threshold: number;
    description: string;
  }>;
  criteria: Criterion[];
  settings: {
    active_profile: string;
    max_refinement_iterations: number;
    enable_input_critique: boolean;
    enable_feedback_loop: boolean;
    show_iteration_history: boolean;
    traffic_light: {
      green_threshold: number;
      orange_threshold: number;
    };
  };
}
