import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Maximize2, Minimize2 } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeViewerProps {
  lines: string[];
  notes?: Record<number, string>;
  isTreeLine: boolean;
  isCurrentStudied: boolean;
  language?: string;
}

export default function CodeViewer({
  lines,
  notes = {},
  isTreeLine,
  isCurrentStudied,
  language = 'text'
}: CodeViewerProps) {
  const [activeLine, setActiveLine] = useState<number | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setActiveLine(null);
  }, [lines]);

  useEffect(() => {
    if (!isExpanded) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsExpanded(false);
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isExpanded]);

  const renderContent = (expanded: boolean) => (
    <div
      role={expanded ? 'dialog' : undefined}
      aria-modal={expanded ? true : undefined}
      aria-label={expanded ? 'Codice sorgente a schermo intero' : undefined}
      className={`flex flex-col justify-between overflow-hidden select-text border border-slate-800 bg-[#111827] shadow-xl shadow-slate-900/10 transition-all duration-300 ${
      expanded 
        ? 'fixed inset-3 z-[100] rounded-2xl p-4 shadow-2xl sm:inset-6 sm:rounded-3xl sm:p-8'
        : 'w-full h-[60vh] min-h-[360px] rounded-2xl p-4 sm:rounded-3xl sm:p-5 lg:p-6 xl:h-full xl:min-h-0'
      }`}
    >

      <div className="flex items-center justify-between pb-4 mb-2 border-b border-white/10 shrink-0">
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-slate-100">
            {isTreeLine ? 'Struttura del progetto' : 'Codice sorgente'}
          </span>
          <span className="mt-1 text-[11px] text-slate-400">
            {isTreeLine ? 'Mappa dei file principali' : 'Seleziona le righe evidenziate per leggere le note'}
          </span>
        </div>

        <button 
          onClick={() => setIsExpanded(!expanded)}
          aria-label={expanded ? 'Riduci il codice' : 'Espandi il codice'}
          className="shrink-0 rounded-lg bg-white/5 p-2 text-slate-300 transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400"
          title={expanded ? 'Riduci' : 'Espandi'}
        >
          {expanded ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
        </button>
      </div>

      <div className="custom-scrollbar min-h-0 flex-1 overflow-auto py-2">
        <SyntaxHighlighter
          language={isTreeLine ? 'text' : language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: 0,
            background: 'transparent',
            fontSize: 'inherit',
            lineHeight: '1.7',
            fontFamily: 'inherit'
          }}
          codeTagProps={{ style: { fontFamily: 'inherit' } }}
          showLineNumbers={!isTreeLine}
          wrapLines
          lineNumberStyle={{ color: '#475569', minWidth: '2.5em', paddingRight: '1em', userSelect: 'none' }}
          lineProps={(lineNumber) => {
            const index = lineNumber - 1;
            const hasNote = Boolean(notes[index]);
            const isSelected = activeLine === index;

            return {
              onClick: () => hasNote && setActiveLine(isSelected ? null : index),
              className: [
                'px-2 lg:px-4 transition-colors whitespace-pre',
                isTreeLine
                  ? 'text-[#98c379] hover:bg-white/[0.02]'
                  : hasNote
                    ? isSelected
                      ? 'bg-sky-500/20 text-white border-l-2 border-sky-300 cursor-pointer'
                      : 'bg-white/[0.04] hover:bg-white/[0.09] border-l-2 border-sky-400/50 cursor-pointer'
                    : 'border-l-2 border-transparent'
              ].join(' ')
            };
          }}
        >
          {lines.join('\n')}
        </SyntaxHighlighter>
      </div>

      {!isTreeLine && (
        <div className="pt-3 mt-2 border-t border-white/10 min-h-13 flex items-center shrink-0">
          {activeLine !== null && notes[activeLine] ? (
            <div className="w-full rounded-xl border border-sky-400/40 bg-[#111c2f] px-3 py-2.5 sm:px-4">
              <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-sky-400 shadow-[0_0_10px_rgba(56,189,248,0.65)]" />
                  <span className="font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-sky-300 sm:text-xs">
                    Line Whisper · Riga {activeLine + 1}
                  </span>
                </div>
                <span className="rounded-full border border-sky-300/20 bg-sky-300/10 px-2 py-0.5 text-[9px] font-medium text-sky-200 sm:text-[10px]">
                  Code insight
                </span>
              </div>
              <p className="text-xs leading-relaxed text-slate-200 sm:text-sm">
                {notes[activeLine]}
              </p>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className={`h-2 w-2 shrink-0 rounded-full ${isCurrentStudied ? 'bg-emerald-400' : 'bg-slate-600'}`} />
              <span className="whitespace-normal">
                {isCurrentStudied
                  ? 'Scheda completata. Puoi proseguire o tornare a rivederla.'
                  : 'Seleziona una riga evidenziata per aprire il Line Whisper.'}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <>
      {renderContent(false)}

      {isExpanded && (
        createPortal(
          <>
            <div
              className="fixed inset-0 z-[90] bg-black/60 backdrop-blur-sm"
              onClick={() => setIsExpanded(false)}
              aria-hidden="true"
            />
            {renderContent(true)}
          </>,
          document.body
        )
      )}
    </>
  );
}