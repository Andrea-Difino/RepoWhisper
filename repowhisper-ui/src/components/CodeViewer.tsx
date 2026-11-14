import { useState, useEffect } from 'react';
import { Lock, Maximize2, Minimize2 } from 'lucide-react';
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

  const renderContent = (expanded: boolean) => (
    <div className={`flex flex-col justify-between overflow-hidden select-text border border-white/5 bg-[#0B0F17] transition-all duration-300 ${
      expanded 
        ? 'fixed inset-6 z-100 rounded-[36px] p-10 shadow-2xl' 
        : 'w-full h-full min-h-0 rounded-[36px] p-5 lg:p-7'
    }`}>

      <div className="flex items-center justify-between pb-4 mb-2 border-b border-white/10 shrink-0">
        <div className="flex flex-col">
          <span className="font-mono text-xs text-slate-400">
            {isTreeLine ? 'Project Architecture' : 'Source Code'}
          </span>
          <span className="text-[11px] font-mono text-slate-500 mt-1">
            {isTreeLine ? 'Struttura ad albero' : 'Clicca sulle righe evidenziate per i dettagli'}
          </span>
        </div>

        <button 
          onClick={() => setIsExpanded(!expanded)}
          className="p-2 bg-white/5 hover:bg-white/10 rounded-full text-slate-300 transition-colors"
          title={expanded ? "Reduce" : "Expand"}
        >
          {expanded ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2 custom-scrollbar min-h-0">
        <SyntaxHighlighter
          language={isTreeLine ? 'text' : language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: 0,
            background: 'transparent',
            fontSize: 'inherit',
            lineHeight: '1.85',
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
                      ? 'bg-blue-500/25 text-white border-l-2 border-blue-400 cursor-pointer'
                      : 'bg-white/[0.04] hover:bg-white/[0.09] border-l-2 border-blue-400/50 cursor-pointer'
                    : 'border-l-2 border-transparent'
              ].join(' ')
            };
          }}
        >
          {lines.join('\n')}
        </SyntaxHighlighter>
      </div>

      {!isTreeLine && (
        <div className="pt-4 mt-2 border-t border-white/10 min-h-13 flex items-center shrink-0">
          {activeLine !== null && notes[activeLine] ? (
            <div className="text-xs lg:text-sm text-slate-200 flex items-center gap-2">
              <span className="text-blue-400 font-mono font-bold">Riga {activeLine + 1} →</span>
              <span className="whitespace-normal">{notes[activeLine]}</span>
            </div>
          ) : (
            <div className="text-xs text-slate-500 flex items-center gap-2">
              {!isCurrentStudied ? (
                <>
                  <Lock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="whitespace-normal">Explore the code and click on <b>studied</b> on the left to unclock the navigation arrow</span>
                </>
              ) : (
                <span className="whitespace-normal">Module completed! Click the right arrow <b>→</b> to go to the next file.</span>
              )}
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
        <>
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-90" 
            onClick={() => setIsExpanded(false)} 
          />
          {renderContent(true)}
        </>
      )}
    </>
  );
}