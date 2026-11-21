import React from 'react';
import { BookOpen, Trash2, X, FileText, ArrowRight, Layers, MapPin, CheckSquare, HelpCircle, Send } from 'lucide-react';
import { translations } from '../translations';

export default function Sidebar({
  schemes,
  onSelectScheme,
  onClearHistory,
  language,
  clearingHistory,
  isOpen,
  onClose,
}) {
  const t = translations[language] || translations.en;

  const getPrefillForScheme = (schemeName) => {
    if (t.prefills[schemeName]) {
      return t.prefills[schemeName];
    }
    return t.prefills.default.replace('{scheme}', schemeName);
  };

  const handleActionClick = (prefillQuery) => {
    onSelectScheme(prefillQuery);
    if (window.innerWidth < 768) onClose();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-72 bg-white border-r border-slate-200 flex flex-col transition-transform duration-300 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        }`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-orange-600" />
            <h2 className="text-sm font-bold text-slate-800">
              {t.schemesSidebarTitle}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="md:hidden p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {/* Schemes Section */}
          <div>
            <p className="px-1 pb-2 text-[11px] font-medium text-slate-500">
              {t.schemesSubtitle}
            </p>
            <div className="space-y-1.5">
              {schemes.length === 0 ? (
                <div className="text-center py-4 px-2 text-xs text-slate-400">
                  <FileText className="w-6 h-6 mx-auto mb-1 opacity-50" />
                  {t.noSchemesFound}
                </div>
              ) : (
                schemes.map((scheme, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleActionClick(getPrefillForScheme(scheme))}
                    className="w-full text-left p-2.5 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-orange-50 hover:border-orange-200 text-slate-700 hover:text-orange-900 transition-all group flex items-start justify-between"
                  >
                    <div className="flex items-start space-x-2">
                      <div className="w-2 h-2 rounded-full bg-orange-400 mt-1.5 flex-shrink-0 group-hover:scale-125 transition-transform" />
                      <div>
                        <div className="text-xs font-semibold leading-snug">
                          {scheme}
                        </div>
                        <div className="text-[10px] text-slate-400 group-hover:text-orange-600 transition-colors mt-0.5">
                          {language === 'ta' ? 'விவரங்களை அறிய தட்டவும்' : 'Click to inquire'}
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-orange-600 opacity-0 group-hover:opacity-100 transition-all transform translate-x-1 group-hover:translate-x-0 mt-1" />
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Quick Application Guide & Centers Section */}
          <div className="pt-2 border-t border-slate-100">
            <div className="flex items-center space-x-1.5 px-1 pb-2">
              <MapPin className="w-3.5 h-3.5 text-emerald-600" />
              <p className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                {t.applyGuideTitle}
              </p>
            </div>
            <div className="space-y-1.5">
              {/* How to Apply */}
              <button
                onClick={() => handleActionClick(t.prefillHowToApply)}
                className="w-full text-left p-2 rounded-xl border border-emerald-100/70 bg-emerald-50/40 hover:bg-emerald-50 hover:border-emerald-300 text-emerald-950 transition-all flex items-center justify-between text-xs font-medium group"
              >
                <div className="flex items-center space-x-2">
                  <BookOpen className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  <span>{t.howToApplyBtn}</span>
                </div>
                <ArrowRight className="w-3 h-3 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>

              {/* Needed Documents */}
              <button
                onClick={() => handleActionClick(t.prefillDocuments)}
                className="w-full text-left p-2 rounded-xl border border-blue-100/70 bg-blue-50/40 hover:bg-blue-50 hover:border-blue-300 text-blue-950 transition-all flex items-center justify-between text-xs font-medium group"
              >
                <div className="flex items-center space-x-2">
                  <CheckSquare className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
                  <span>{t.documentsBtn}</span>
                </div>
                <ArrowRight className="w-3 h-3 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>

              {/* Nearest Centers */}
              <button
                onClick={() => handleActionClick(t.prefillCenters)}
                className="w-full text-left p-2 rounded-xl border border-purple-100/70 bg-purple-50/40 hover:bg-purple-50 hover:border-purple-300 text-purple-950 transition-all flex items-center justify-between text-xs font-medium group"
              >
                <div className="flex items-center space-x-2">
                  <MapPin className="w-3.5 h-3.5 text-purple-600 flex-shrink-0" />
                  <span className="truncate">{t.centersBtn}</span>
                </div>
                <ArrowRight className="w-3 h-3 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              </button>

              {/* Apply via this Portal? */}
              <button
                onClick={() => handleActionClick(t.prefillPortalApply)}
                className="w-full text-left p-2 rounded-xl border border-amber-100/70 bg-amber-50/40 hover:bg-amber-50 hover:border-amber-300 text-amber-950 transition-all flex items-center justify-between text-xs font-medium group"
              >
                <div className="flex items-center space-x-2">
                  <HelpCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                  <span>{t.portalApplyBtn}</span>
                </div>
                <ArrowRight className="w-3 h-3 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar Footer: Clear Chat */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/50">
          <button
            onClick={onClearHistory}
            disabled={clearingHistory}
            className="w-full flex items-center justify-center space-x-2 py-2 px-3 text-xs font-medium text-red-600 hover:text-red-700 bg-white hover:bg-red-50 border border-red-200 rounded-xl transition-all shadow-sm disabled:opacity-50"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{clearingHistory ? t.clearingHistory : t.clearHistoryBtn}</span>
          </button>
        </div>
      </aside>
    </>
  );
}
