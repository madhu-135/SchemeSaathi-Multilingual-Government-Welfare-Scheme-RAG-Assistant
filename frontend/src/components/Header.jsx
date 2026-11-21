import React from 'react';
import { Sparkles, Globe, Menu, ShieldCheck } from 'lucide-react';
import { translations } from '../translations';

export default function Header({
  language,
  setLanguage,
  systemStatus,
  onToggleSidebar,
}) {
  const t = translations[language] || translations.en;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Left: Mobile hamburger & App Brand */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle Sidebar"
            className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors focus:outline-none"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-orange-500 via-amber-500 to-green-600 flex items-center justify-center text-white font-bold shadow-md flex-shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-1.5">
                  {language === 'ta' ? 'திட்ட தோழன்' : 'SchemeSaathi'}
                </h1>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-orange-100 text-orange-800 border border-orange-200">
                  {language === 'ta' ? 'SchemeSaathi' : 'திட்ட தோழன்'}
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                {t.appSubtitle}
              </p>
            </div>
          </div>
        </div>

        {/* Right: Language switch & System status */}
        <div className="flex items-center space-x-3">
          {/* Language Toggle */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs shadow-inner">
            <Globe className="w-3.5 h-3.5 text-slate-500 ml-1.5 mr-1" />
            <button
              onClick={() => setLanguage('en')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                language === 'en'
                  ? 'bg-white text-slate-900 shadow-sm font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              English
            </button>
            <button
              onClick={() => setLanguage('ta')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                language === 'ta'
                  ? 'bg-white text-slate-900 shadow-sm font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              தமிழ்
            </button>
          </div>

          {/* Backend Health Pill */}
          <div className="hidden sm:flex items-center text-xs px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200 text-slate-600">
            <span
              className={`w-2 h-2 rounded-full mr-1.5 ${
                systemStatus?.status === 'healthy'
                  ? 'bg-green-500 ring-2 ring-green-100'
                  : systemStatus?.status === 'degraded'
                  ? 'bg-amber-500 ring-2 ring-amber-100'
                  : 'bg-red-500 ring-2 ring-red-100'
              }`}
            />
            <span>
              {systemStatus?.status === 'healthy'
                ? 'Online'
                : systemStatus?.status === 'degraded'
                ? 'Active'
                : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

