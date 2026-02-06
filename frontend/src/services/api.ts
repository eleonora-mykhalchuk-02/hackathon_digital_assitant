/* API client for backend communication */

import type {
  ChatRequest,
  ChatResponse,
  CriteriaConfig,
  Message
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getConversationHistory(conversationId: string): Promise<{ conversation_id: string; messages: Message[] }> {
    return this.request(`/api/chat/history/${conversationId}`);
  }

  async getCriteria(): Promise<CriteriaConfig> {
    return this.request<CriteriaConfig>('/api/criteria');
  }

  async updateCriteria(criteria: Partial<CriteriaConfig>): Promise<{ message: string }> {
    return this.request('/api/criteria', {
      method: 'PUT',
      body: JSON.stringify(criteria),
    });
  }

  async health(): Promise<{ status: string; chatbot_model: string; judge_model: string }> {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient();
