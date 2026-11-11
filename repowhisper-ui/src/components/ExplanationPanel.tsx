/* eslint-disable @typescript-eslint/no-unused-vars */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ModuleData {
  path: string;
  title: string;
  explanation: string;
}

interface ExplanationPanelProps {
  module: ModuleData;
}

export default function ExplanationPanel({ module }: ExplanationPanelProps) {
  return (
    // Il contenitore esterno prende l'altezza disponibile (meno i 52px del bottone) ed è rigorosamente nascosto l'overflow
    <div className="w-full h-100 bg-[#F4F4F4] rounded-[36px] p-2 lg:p-4 overflow-hidden">
      
      {/* Il contenitore interno gestisce lo scroll (overflow-y-auto) senza far esplodere la card madre */}
      <div className="w-full max-h-[calc(100%-5px)] rounded-[26px] p-5 lg:p-7 flex flex-col overflow-y-auto select-text bg-[#F4F4F4] custom-scrollbar">
        
        <div className="flex items-center justify-between gap-2 mb-2 shrink-0">
          <span className="font-mono text-xs text-black/50">
            {module.path}
          </span>
        </div>

        <h2 className="text-2xl lg:text-[28px] font-bold tracking-tight text-[#11151C] mb-5 uppercase leading-snug shrink-0">
          {module.title}
        </h2>

        <div className="prose prose-sm lg:prose-base prose-slate max-w-none text-[#222] prose-headings:text-xs prose-headings:uppercase prose-headings:tracking-widest prose-headings:text-black/50 prose-headings:mt-5 prose-headings:mb-2 prose-p:leading-relaxed prose-li:my-0.5">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Stili di base
              ul: ({ node, ...props }) => <ul className="list-disc pl-6 my-4 space-y-2 marker:text-black/40" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal pl-6 my-4 space-y-2 marker:text-black/40" {...props} />,
              li: ({ node, ...props }) => <li className="text-[#222] leading-relaxed" {...props} />,
              p: ({ node, ...props }) => <p className="mb-4 leading-relaxed text-[#222]" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold text-[#11151C]" {...props} />,
              // Nuovi stili per le Tabelle (bellissime e responsive)
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-6 rounded-xl border border-black/10 bg-white">
                  <table className="w-full text-left border-collapse text-sm" {...props} />
                </div>
              ),
              thead: ({ node, ...props }) => <thead className="bg-black/5 border-b border-black/10" {...props} />,
              tr: ({ node, ...props }) => <tr className="border-b border-black/5 last:border-0 hover:bg-black/[0.02] transition-colors" {...props} />,
              th: ({ node, ...props }) => <th className="py-3 px-4 font-semibold text-black/70 whitespace-nowrap" {...props} />,
              td: ({ node, ...props }) => <td className="py-3 px-4 text-black/80 align-top" {...props} />,
              // Stile per il codice inline
              code: ({ node, inline, ...props }: any) => 
                inline 
                  ? <code className="bg-black/5 text-pink-600 px-1.5 py-0.5 rounded-md font-mono text-[0.85em]" {...props} />
                  : <code {...props} />
            }}
          >
            {module.explanation}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}