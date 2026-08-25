export type ChatSource = {
  title: string;
  type: string;
  relevancy: string;
  score: number;
  snippet?: string | null;
  uri?: string | null;
};

export type ChatTurn = {
  role: 'user' | 'assistant';
  content: string;
};

export type ChatEvent = {
  messagetype?: string | null;
  class?: string | null;
  content?: string | null;
  apiname?: string | null;
  additionalinfotags?: string | null;
  additionalinfousecase?: string | null;
  createddate?: string | null;
};

export type ChatResponse = {
  session_id: string;
  message_id: string;
  answer: string;
  sources: ChatSource[];
  suggestions: string[];
  use_case: string;
  tool_used: string;
  reflexion_iterations: number;
  events: ChatEvent[];
};

export type ChatRequest = {
  query: string;
  session_id?: string;
  user_id?: string;
  bubble?: string;
  history: ChatTurn[];
};

export type ChatMessage = ChatTurn & {
  id: string;
  createdAt: number;
  sources?: ChatSource[];
  suggestions?: string[];
  useCase?: string;
  toolUsed?: string;
  events?: ChatEvent[];
};
