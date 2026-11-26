import { ArrowLeft, ArrowRight } from 'lucide-react';
import type { ModuleNavItem } from '../types';
import ModuleIndex from './ModuleIndex';
import StudyButton from './StudyButton';

interface TopBarProps {
  repositoryTitle: string;
  currentIndex: number;
  totalFiles: number;
  studiedCount: number;
  modules: ModuleNavItem[];
  canGoPrev: boolean;
  canGoNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  onSelectModule: (index: number) => void;
  isStudied: boolean;
  isFirstSlide: boolean;
  showStudyButton: boolean;
  onToggleStudy: () => void;
}

export default function TopBar({
  repositoryTitle,
  currentIndex,
  totalFiles,
  studiedCount,
  modules,
  canGoPrev,
  canGoNext,
  onPrev,
  onNext,
  onSelectModule,
  isStudied,
  isFirstSlide,
  showStudyButton,
  onToggleStudy
}: TopBarProps) {
  const progress = totalFiles > 0 ? (studiedCount / totalFiles) * 100 : 100;

  return (
    <header className="relative z-30 w-full border-b border-slate-200/80 bg-white/90 shadow-sm shadow-slate-900/[0.03] backdrop-blur">
      <div className="mx-auto max-w-[1700px] px-4 py-3 sm:px-6 sm:py-4 xl:px-12">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <img
              src="/logo_sfondo_blu.png"
              className="h-14 w-20 rounded-xl object-cover"
              alt="RepoWhisper"
            />
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                Sessione di studio
              </p>
              <p className="truncate text-base font-bold text-slate-800 sm:text-lg">
                {repositoryTitle}
              </p>
            </div>
          </div>

          <div className="w-full sm:max-w-64">
            <div className="mb-1.5 flex items-center justify-between gap-3 text-xs">
              <span className="font-medium text-slate-500">Progresso</span>
              <span className="font-semibold tabular-nums text-slate-700">
                {studiedCount} <span className="font-normal text-slate-400">/ {totalFiles} completate</span>
              </span>
            </div>
            <div
              className="h-2 overflow-hidden rounded-full bg-slate-100"
              role="progressbar"
              aria-label="Progresso delle schede"
              aria-valuenow={studiedCount}
              aria-valuemin={0}
              aria-valuemax={Math.max(totalFiles, 1)}
            >
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-[width] duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <div className="flex flex-wrap items-center justify-end gap-2">
            <button
              type="button"
              onClick={onPrev}
              disabled={!canGoPrev}
              aria-label="Scheda precedente"
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>

            <ModuleIndex
              items={modules}
              currentIndex={currentIndex}
              onSelect={onSelectModule}
            />

            <button
              type="button"
              onClick={onNext}
              disabled={!canGoNext}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              {currentIndex === totalFiles ? 'Termina' : 'Avanti'}
              <ArrowRight className="h-4 w-4" />
            </button>

            {showStudyButton && (
              <StudyButton
                isStudied={isStudied}
                isFirstSlide={isFirstSlide}
                onClick={onToggleStudy}
              />
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
