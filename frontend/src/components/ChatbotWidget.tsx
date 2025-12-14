import { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getOrCreateGuestId } from '../utils/guestId';

interface Message {
  role: 'user' | 'assistant';
  message: string;
  timestamp: Date;
}

export function ChatbotWidget() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session ID from localStorage
  useEffect(() => {
    const storedSessionId = localStorage.getItem('chat_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
      loadChatHistory(storedSessionId);
    } else {
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      localStorage.setItem('chat_session_id', newSessionId);
      
      // Send initial Gemini-powered greeting
      const greeting: Message = {
        role: 'assistant',
        message: "Hello! 👋 I'm Hanco AI Assistant, powered by advanced AI.\n\nI can help you with:\n🚗 Finding the perfect vehicle\n💰 Pricing & comparisons\n📅 Checking availability\n📍 Locations & services\n❓ Answering your questions\n\nWhat would you like to know?",
        timestamp: new Date()
      };
      setMessages([greeting]);
      saveChatHistory([greeting]);
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadChatHistory = (sid: string) => {
    const stored = localStorage.getItem(`chat_history_${sid}`);
    if (stored) {
      try {
        const history = JSON.parse(stored);
        setMessages(history.map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) })));
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
  };

  const saveChatHistory = (msgs: Message[]) => {
    if (sessionId) {
      localStorage.setItem(`chat_history_${sessionId}`, JSON.stringify(msgs));
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { 
      role: 'user', 
      message: input,
      timestamp: new Date()
    };
    
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setLoading(true);

    try {
      // Get guest ID for authentication
      const guestId = getOrCreateGuestId();
      
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      // Call Gemini-powered backend API with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
      
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Guest-Id': guestId
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: input
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: 'assistant',
        message: data.reply,
        timestamp: new Date()
      };

      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      saveChatHistory(finalMessages);
      
      // Log intent for debugging
      if (data.intent) {
        console.log('Gemini detected intent:', data.intent, data.extracted);
      }
    } catch (error) {
      console.error('Chat error:', error);
      let errorMsg = '🧠 Sorry, I encountered an error connecting to my AI brain. Please try again or visit our Booking page directly.';
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMsg = '⏱️ Request timed out. The AI service might be starting up. Please try again in a moment.';
        } else if (error.message.includes('Failed to fetch')) {
          errorMsg = '🔌 Unable to connect to the backend service. Please check if the backend is running and try again.';
        }
      }
      
      const errorMessage: Message = {
        role: 'assistant',
        message: errorMsg,
        timestamp: new Date()
      };
      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      saveChatHistory(finalMessages);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    if (window.confirm('Clear chat history?')) {
      setMessages([]);
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      localStorage.setItem('chat_session_id', newSessionId);
      localStorage.removeItem(`chat_history_${sessionId}`);
      
      // Add greeting after clear
      const greeting: Message = {
        role: 'assistant',
        message: "Hello! 👋 I'm Hanco AI Assistant. How can I help you today?",
        timestamp: new Date()
      };
      setMessages([greeting]);
      saveChatHistory([greeting]);
    }
  };

  // Render message content with markdown-style formatting
  const renderMessageContent = (msg: Message) => {
    const message = msg.message;
    
    // Split by double newlines for paragraphs
    const paragraphs = message.split('\n\n');
    
    return (
      <div className="space-y-2">
        {paragraphs.map((para, idx) => {
          // Check if it contains a booking link
          if (para.includes('[Book Now]')) {
            const linkMatch = para.match(/\[Book Now\]\((.*?)\)/);
            if (linkMatch) {
              const url = linkMatch[1];
              return (
                <div key={idx} className="mt-3">
                  <a 
                    href={url} 
                    className="inline-block bg-red-700 text-white px-6 py-3 rounded-lg hover:bg-red-800 transition-colors font-semibold"
                    onClick={() => setIsOpen(false)}
                  >
                    🚗 Complete Booking
                  </a>
                </div>
              );
            }
          }
          
          // Check if it's a list
          if (para.includes('\n•') || para.includes('\n✓') || para.includes('\n🚗') || para.includes('\n💰') || para.includes('\n  •')) {
            const lines = para.split('\n');
            let title = lines[0];
            const items = lines.slice(1);
            
            // Handle **bold** markdown in title
            const boldMatch = title.match(/\*\*(.+?)\*\*/);
            if (boldMatch) {
              const parts = title.split(/\*\*(.+?)\*\*/);
              title = parts.filter(p => p).join('');
            }
            
            return (
              <div key={idx}>
                {title && <p className="font-bold mb-1">{title}</p>}
                <ul className="space-y-1 ml-2">
                  {items.map((item, i) => (
                    item.trim() && <li key={i} className="text-sm">{item}</li>
                  ))}
                </ul>
              </div>
            );
          }
          
          // Check for numbered lists (1️⃣, 2️⃣, etc.)
          if (para.match(/\d️⃣/)) {
            const lines = para.split('\n');
            return (
              <div key={idx} className="space-y-1">
                {lines.map((line, i) => (
                  line.trim() && <div key={i} className="text-sm">{line}</div>
                ))}
              </div>
            );
          }
          
          // Handle **bold** text in regular paragraphs
          if (para.includes('**')) {
            const parts = para.split(/(\*\*.+?\*\*)/);
            return (
              <p key={idx} className="text-sm whitespace-pre-line">
                {parts.map((part, i) => {
                  if (part.startsWith('**') && part.endsWith('**')) {
                    return <strong key={i}>{part.slice(2, -2)}</strong>;
                  }
                  return part;
                })}
              </p>
            );
          }
          
          // Regular paragraph
          return para.trim() && <p key={idx} className="text-sm whitespace-pre-line">{para}</p>;
        })}
      </div>
    );
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-gradient-to-r from-red-700 to-red-800 text-white p-4 rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-110 z-50 group"
          aria-label="Open chat"
        >
          <MessageCircle className="h-6 w-6" />
          <span className="absolute -top-1 -right-1 bg-green-500 w-3 h-3 rounded-full animate-pulse"></span>
          <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block">
            <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 whitespace-nowrap">
              Ask me anything! 🤖
            </div>
          </div>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50 border border-gray-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-red-700 to-red-800 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-5 w-5 animate-pulse" />
              <div>
                <h3 className="font-semibold">Hanco AI Assistant</h3>
                <p className="text-xs text-red-100">Powered by Gemini AI</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-red-900 p-1 rounded transition-colors"
              aria-label="Close chat"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-red-700 text-white'
                      : 'bg-white border border-gray-200 text-gray-800'
                  }`}
                >
                  {renderMessageContent(msg)}
                  <p className="text-xs opacity-70 mt-1">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
            <div className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && sendMessage()}
                placeholder="Ask me anything..."
                className="input flex-1 text-sm"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="bg-red-700 text-white p-2 rounded-lg hover:bg-red-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Send message"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                Powered by Gemini AI
              </p>
              <button
                onClick={clearChat}
                className="text-xs text-red-600 hover:text-red-800 transition-colors"
              >
                Clear chat
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
