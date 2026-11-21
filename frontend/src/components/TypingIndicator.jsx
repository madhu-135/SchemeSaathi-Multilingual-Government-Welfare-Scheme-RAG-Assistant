import React from 'react';
import { Bot } from 'lucide-react';
import { translations } from '../translations';

export default function TypingIndicator({ language }) {
  const t = translations[language] || translations.en;

  return (
    <div className="flex gap-3 my-3 justify-start animate-fadeIn">
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-orange-500 to-amber-500 text-white flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
        <Bot className="w-4 h-4" />
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm flex items-center space-x-3">
        <div className="flex space-x-1.5 items-center">
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-bounce [animation-delay:-0.3s]" />
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-bounce [animation-delay:-0.15s]" />
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-bounce" />
        </div>
        <span className="text-xs text-slate-500 font-medium">
          {t.searching}
        </span>
      </div>
    </div>
  );
}

