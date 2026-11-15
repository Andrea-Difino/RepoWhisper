import { Check, Sparkles } from 'lucide-react';

interface CompletionPageProps {
  repositoryTitle: string;
  studiedFiles: number;
  totalFiles: number;
}

export default function CompletionPage({
  repositoryTitle,
  studiedFiles,
  totalFiles
}: CompletionPageProps) {
  return (
    <div className="w-full px-8 py-6 text-center lg:py-10">
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-[#4E7D34]/10 text-[#4E7D34]">
        <Sparkles className="h-7 w-7" strokeWidth={1.8} />
      </div>

      <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-black/45">
        Studio completato
      </p>
      <h1 className="mb-5 text-3xl font-bold tracking-tight text-[#11151C] lg:text-5xl">
        Ottimo lavoro!
      </h1>
      <p className="mx-auto max-w-xl text-base leading-relaxed text-black/65 lg:text-lg">
        Hai esplorato <strong className="text-[#11151C]">{repositoryTitle}</strong> e
        completato tutti i moduli disponibili.
      </p>

      <div className="mx-auto mt-7 inline-flex items-center gap-2 text-sm font-medium text-[#4E7D34]">
        <Check className="h-4 w-4" strokeWidth={3} />
        {studiedFiles} / {totalFiles} file studiati
      </div>

      <p className="mt-6 text-sm text-black/45">
        Puoi tornare indietro per rivedere qualsiasi modulo.
      </p>
    </div>
  );
}
