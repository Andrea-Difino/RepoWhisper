/* eslint-disable @typescript-eslint/no-unused-vars */
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ModuleData } from '../types';

interface ExplanationPanelProps {
  module: ModuleData;
  isOverview?: boolean;
}

export default function ExplanationPanel({ module, isOverview = false }: ExplanationPanelProps) {
  return (
    <section className="w-full rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-900/[0.03] sm:rounded-3xl sm:p-6 xl:h-full xl:overflow-hidden">
      
      <div className="flex w-full flex-col select-text xl:max-h-full xl:overflow-y-auto custom-scrollbar">
        
        <div className="flex items-center justify-between gap-2 mb-2 shrink-0">
          <span className="max-w-full truncate rounded-md bg-slate-100 px-2 py-1 font-mono text-[11px] text-slate-500">
            {module.path}
          </span>
        </div>

        <h2 className={`${isOverview ? 'text-3xl sm:text-4xl' : 'text-2xl'} mb-4 break-words font-bold leading-tight tracking-tight text-slate-900 sm:mb-5`}>
          {module.title}
        </h2>

        <div className="prose prose-slate max-w-none text-sm leading-relaxed text-slate-600 prose-headings:mt-5 prose-headings:mb-2 prose-headings:text-xs prose-headings:font-semibold prose-headings:uppercase prose-headings:tracking-widest prose-headings:text-slate-500 prose-p:mb-4 prose-p:leading-relaxed prose-li:my-1 prose-strong:text-slate-800">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              ul: ({ node, ...props }) => <ul className="list-disc pl-6 my-4 space-y-2 marker:text-black/40" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal pl-6 my-4 space-y-2 marker:text-black/40" {...props} />,
              li: ({ node, ...props }) => <li className="text-[#222] leading-relaxed" {...props} />,
              p: ({ node, ...props }) => <p className="mb-4 leading-relaxed text-[#222]" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold text-[#11151C]" {...props} />,
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-6 rounded-xl border border-black/10 bg-white">
                  <table className="w-full text-left border-collapse text-sm" {...props} />
                </div>
              ),
              thead: ({ node, ...props }) => <thead className="bg-black/5 border-b border-black/10" {...props} />,
              tr: ({ node, ...props }) => <tr className="border-b border-black/5 last:border-0 hover:bg-black/2 transition-colors" {...props} />,
              th: ({ node, ...props }) => <th className="py-3 px-4 font-semibold text-black/70 whitespace-nowrap" {...props} />,
              td: ({ node, ...props }) => <td className="py-3 px-4 text-black/80 align-top" {...props} />,
              pre: ({ node, ...props }) => (
                <pre className="max-w-full overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs leading-6 text-slate-100" {...props} />
              ),
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              code: ({ node, inline, ...props }: any) => 
                inline 
                  ? <code className="rounded bg-indigo-50 px-1.5 py-0.5 font-mono text-[0.85em] text-indigo-700" {...props} />
                  : <code {...props} />
            }}
          >
            {module.explanation}
          </ReactMarkdown>
        </div>
      </div>
    </section>
  );
}