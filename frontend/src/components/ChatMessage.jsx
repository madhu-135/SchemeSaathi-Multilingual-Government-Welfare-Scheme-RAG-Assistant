import React, { useState } from 'react';
import { Bot, User, BookOpen, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { translations } from '../translations';

export default function ChatMessage({ message, language }) {
  const isUser = message.role === 'user';
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const t = translations[language] || translations.en;
  const hasSources = message.sources && message.sources.length > 0;

  return (
    <div className={`flex gap-3 my-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Bot Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-orange-500 to-amber-500 text-white flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
          <Bot className="w-4 h-4" />
        </div>
      )}

      {/* Message Bubble Container */}
      <div
        className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-4 py-3 shadow-sm transition-all ${
          isUser
            ? 'bg-orange-600 text-white rounded-br-sm'
            : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm'
        }`}
      >
        {/* Markdown Text */}
        <div
          className={`prose prose-sm max-w-none break-words text-sm leading-relaxed ${
            isUser ? 'text-white prose-invert' : 'text-slate-800'
          }`}
        >
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Collapsible Sources Panel (Bot messages only) */}
        {!isUser && hasSources && (
          <div className="mt-3 pt-2.5 border-t border-slate-100">
            <button
              onClick={() => setSourcesOpen((prev) => !prev)}
              className="flex items-center justify-between w-full text-xs font-semibold text-slate-600 hover:text-orange-700 bg-slate-50 hover:bg-orange-50 px-2.5 py-1.5 rounded-lg border border-slate-200 transition-colors"
            >
              <div className="flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-orange-600" />
                <span>
                  {t.sourcesTitle} ({message.sources.length})
                </span>
              </div>
              {sourcesOpen ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            {/* Collapsible Accordion Content */}
            {sourcesOpen && (
              <div className="mt-2 space-y-2 animate-fadeIn">
                {message.sources.map((src, i) => (
                  <div
                    key={i}
                    className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between flex-wrap gap-1">
                      <div className="font-semibold text-slate-800 flex items-center space-x-1">
                        <FileText className="w-3 h-3 text-slate-400" />
                        <span>{src.scheme_name}</span>
                      </div>
                      <div className="flex items-center space-x-2 text-[11px]">
                        <span className="text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                          {t.pageLabel} {src.page_number}
                        </span>
                        {src.score && (
                          <span className="text-orange-700 font-medium bg-orange-100 px-1.5 py-0.5 rounded">
                            {(src.score * 100).toFixed(0)}% match
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-slate-600 italic bg-white p-2 rounded-lg border border-slate-100 line-clamp-3">
                      "{src.snippet}"
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div
          className={`text-[10px] mt-1.5 text-right ${
            isUser ? 'text-orange-200' : 'text-slate-400'
          }`}
        >
          {message.timestamp}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-700 text-white flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
}

