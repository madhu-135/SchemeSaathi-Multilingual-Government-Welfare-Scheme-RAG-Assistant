import React, { useState, useEffect, useRef } from 'react';
import { Send, AlertTriangle, RefreshCw, Sparkles, FileText } from 'lucide-react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatMessage from './components/ChatMessage';
import TypingIndicator from './components/TypingIndicator';
import { translations } from './translations';

// API base URL: defaults to empty string (same-origin / reverse proxy), or custom URL via VITE_API_BASE_URL
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export default function App() {
  // Session ID persistence in localStorage
  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem('schemesaathi_session_id');
    if (saved) return saved;
    const newId = 'citizen_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('schemesaathi_session_id', newId);
    return newId;
  });

  // Language state persistence in localStorage
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('schemesaathi_language') || 'en';
  });

  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [schemes, setSchemes] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const t = translations[language] || translations.en;

  // Persist language preference
  const handleSetLanguage = (newLang) => {
    setLanguage(newLang);
    localStorage.setItem('schemesaathi_language', newLang);
  };

  // Scroll to bottom on new message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load schemes and backend health on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => setSystemStatus(data))
      .catch(() => setSystemStatus({ status: 'offline' }));

    fetch(`${API_BASE}/schemes`)
      .then((res) => res.json())
      .then((data) => {
        if (data && Array.isArray(data.schemes)) {
          setSchemes(data.schemes);
        } else if (Array.isArray(data)) {
          setSchemes(data);
        }
      })
      .catch(() => setSchemes([]));
  }, []);

  // Load session history from backend or show welcome message
  useEffect(() => {
    let isMounted = true;
    fetch(`${API_BASE}/history/${sessionId}`)
      .then((res) => {
        if (!res.ok) throw new Error('No prior history');
        return res.json();
      })
      .then((data) => {
        if (isMounted && data.messages && data.messages.length > 0) {
          const loaded = data.messages.map((m, idx) => ({
            id: `hist_${idx}`,
            role: m.role,
            content: m.content,
            sources: m.sources || [],
            timestamp: new Date(m.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            }),
          }));
          setMessages(loaded);
        } else if (isMounted) {
          setMessages([
            {
              id: 'welcome',
              role: 'assistant',
              content: t.welcomeGreeting,
              sources: [],
              timestamp: new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              }),
            },
          ]);
        }
      })
      .catch(() => {
        if (isMounted) {
          setMessages([
            {
              id: 'welcome',
              role: 'assistant',
              content: t.welcomeGreeting,
              sources: [],
              timestamp: new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              }),
            },
          ]);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [sessionId, language]);

  // Submit a query
  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputQuery;
    if (!text.trim() || loading) return;

    setErrorMessage(null);
    const nowTime = new Date().toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });

    const userMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: nowTime,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question: text,
        }),
      });

      if (response.status === 429) {
        throw new Error('RATE_LIMIT');
      }

      if (!response.ok) {
        throw new Error(`SERVER_ERROR_${response.status}`);
      }

      const data = await response.json();

      const botMessage = {
        id: `bot_${Date.now()}`,
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        chunk_ids: data.chunk_ids || [],
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      if (err.message === 'RATE_LIMIT') {
        setErrorMessage(t.rateLimitError);
      } else {
        setErrorMessage(t.serverOffline);
      }
    } finally {
      setLoading(false);
    }
  };

  // Prefill input from sidebar scheme click
  const handleSelectScheme = (prefillQuestion) => {
    setInputQuery(prefillQuestion);
    inputRef.current?.focus();
  };

  // Clear chat history & reset session
  const handleClearHistory = async () => {
    setClearingHistory(true);
    setErrorMessage(null);
    try {
      await fetch(`${API_BASE}/history/${sessionId}`, { method: 'DELETE' });
    } catch (err) {
      // Ignore network errors when clearing
    }

    // Generate fresh session ID
    const newSessionId = 'citizen_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('schemesaathi_session_id', newSessionId);
    setSessionId(newSessionId);

    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: t.welcomeGreeting,
        sources: [],
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      },
    ]);
    setClearingHistory(false);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-100 font-sans text-slate-900">
      {/* Top Navbar */}
      <Header
        language={language}
        setLanguage={handleSetLanguage}
        systemStatus={systemStatus}
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
      />

      {/* Main Body with Sidebar + Chat Area */}
      <div className="flex-1 flex overflow-hidden max-w-7xl w-full mx-auto">
        {/* Left Schemes Sidebar */}
        <Sidebar
          schemes={schemes}
          onSelectScheme={handleSelectScheme}
          onClearHistory={handleClearHistory}
          language={language}
          clearingHistory={clearingHistory}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Chat Window Container */}
        <main className="flex-1 flex flex-col bg-slate-50 overflow-hidden relative">
          {/* Error Banner */}
          {errorMessage && (
            <div className="bg-red-50 border-b border-red-200 px-4 py-2.5 flex items-center justify-between text-xs text-red-700 animate-fadeIn">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <button
                onClick={() => setErrorMessage(null)}
                className="text-red-500 hover:text-red-800 font-bold ml-2"
              >
                ✕
              </button>
            </div>
          )}

          {/* Messages List Area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} language={language} />
            ))}

            {loading && <TypingIndicator language={language} />}
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Chat Input Form */}
          <div className="p-3 sm:p-4 bg-white border-t border-slate-200">
            <div className="max-w-4xl mx-auto">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2 bg-slate-50 border border-slate-300 focus-within:border-orange-500 focus-within:ring-2 focus-within:ring-orange-100 rounded-2xl p-1.5 transition-all shadow-sm"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder={t.inputPlaceholder}
                  disabled={loading}
                  className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={!inputQuery.trim() || loading}
                  className={`p-2.5 rounded-xl transition-all flex items-center justify-center ${inputQuery.trim() && !loading
                      ? 'bg-orange-600 hover:bg-orange-700 text-white shadow-md active:scale-95'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    }`}
                  aria-label={t.sendBtn}
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>

              <p className="text-[11px] text-center text-slate-400 mt-2">
                {t.disclaimer}
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
