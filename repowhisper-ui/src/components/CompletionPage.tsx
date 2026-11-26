import { ArrowRight, Check, RotateCcw, Sparkles } from 'lucide-react';

interface CompletionPageProps {
  repositoryTitle: string;
  studiedFiles: number;
  totalFiles: number;
  onResumeIncomplete: () => void;
}

export default function CompletionPage({
  repositoryTitle,
  studiedFiles,
  totalFiles,
  onResumeIncomplete
}: CompletionPageProps) {
  const allStudied = studiedFiles === totalFiles;

  return (
    <div className="mx-auto w-full max-w-2xl rounded-3xl border border-slate-200 bg-white px-6 py-10 text-center shadow-sm sm:px-10">
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
        {allStudied
          ? <Sparkles className="h-7 w-7" strokeWidth={1.8} />
          : <Check className="h-7 w-7" strokeWidth={2} />}
      </div>

      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">
        {allStudied ? 'Studio completato' : 'Fine del percorso'}
      </p>
      <h2 className="mb-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
        {allStudied ? 'Ottimo lavoro!' : 'Hai fatto un bel tratto.'}
      </h2>
      <p className="mx-auto max-w-xl text-base leading-relaxed text-slate-600">
        {allStudied
          ? <>Hai completato tutte le schede di <strong className="text-slate-900">{repositoryTitle}</strong>.</>
          : <>Hai esplorato <strong className="text-slate-900">{repositoryTitle}</strong>. Puoi riprendere le schede che hai lasciato in sospeso.</>}
      </p>

      <div className="mx-auto mt-7 inline-flex items-center gap-2 rounded-full bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">
        <Check className="h-4 w-4 text-emerald-600" strokeWidth={3} />
        {studiedFiles} di {totalFiles} schede completate
      </div>

      <button
        type="button"
        onClick={onResumeIncomplete}
        className="mx-auto mt-7 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
      >
        {allStudied ? 'Rivedi la panoramica' : 'Riprendi le schede in sospeso'}
        {allStudied ? <RotateCcw className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
      </button>
    </div>
  );
}
