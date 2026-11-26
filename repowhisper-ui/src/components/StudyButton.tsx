import { Check, Circle } from 'lucide-react';

interface StudyButtonProps {
  isStudied: boolean;
  isFirstSlide: boolean;
  onClick: () => void;
}

export default function StudyButton({ isStudied, isFirstSlide, onClick }: StudyButtonProps) {
  return (
    <button
      onClick={onClick}
      type="button"
      aria-pressed={isStudied}
      className={`inline-flex h-10 items-center gap-2 rounded-xl border px-3 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 ${
        isStudied 
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
          : 'border-emerald-600 bg-white text-emerald-700 hover:bg-emerald-50'
      }`}
    >
      {isStudied
        ? <Check className="h-4 w-4" strokeWidth={2.5} />
        : <Circle className="h-4 w-4" strokeWidth={1.8} />}
      <span>{isStudied ? 'Completata' : isFirstSlide ? 'Segna panoramica' : 'Segna completata'}</span>
    </button>
  );
}