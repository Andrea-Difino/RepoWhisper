import { ArrowLeft, ArrowRight } from 'lucide-react';
import StudyButton from './StudyButton';

interface TopBarProps {
  currentIndex: number;
  totalFiles: number;
  canGoPrev: boolean;
  canGoNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  isStudied: boolean;
  isFirstSlide: boolean;
  showStudyButton: boolean;
  onToggleStudy: () => void;
}

export default function TopBar({ 
  currentIndex, 
  totalFiles, 
  canGoPrev, 
  canGoNext, 
  onPrev, 
  onNext,
  isStudied,
  isFirstSlide,
  showStudyButton,
  onToggleStudy
}: TopBarProps) {
  return (
    <header className="w-full max-w-360 h-[15vh] mt-6 mx-auto px-12 flex flex-col items-center justify-end z-10 gap-3">
      <div className="flex items-center gap-4">
        <span className="text-[15px] font-mono font-normal bg-black/5 text-black/60 px-4 py-2 rounded-full">
          {currentIndex > totalFiles ? 'COMPLETATO' : currentIndex === 0 ? 'START' : `${currentIndex} / ${totalFiles}`}
        </span>
      </div>

      <div className="flex flex-col items-center gap-1">
        <div className="flex items-center gap-4 mb-1">
        <button
          onClick={onPrev}
          disabled={!canGoPrev}
          className={`w-12 h-12 rounded-full border flex items-center justify-center transition-all duration-200 ${
            canGoPrev
              ? 'border-[#11151C] text-[#11151C] hover:bg-[#11151C] hover:text-white cursor-pointer active:scale-95'
              : 'border-black/20 text-black/20 cursor-not-allowed'
          }`}
        >
          <ArrowLeft className="w-5 h-5" strokeWidth={1.8} />
        </button>

        <button
          onClick={onNext}
          disabled={!canGoNext}
          className={`w-12 h-12 rounded-full border flex items-center justify-center transition-all duration-200 ${
            canGoNext
              ? 'border-[#11151C] text-[#11151C] hover:bg-[#11151C] hover:text-white cursor-pointer shadow-sm active:scale-95'
              : 'border-black/20 text-black/25 cursor-not-allowed'
          }`}
        >
          <ArrowRight className="w-5 h-5" strokeWidth={1.8} />
        </button>
        </div>

        {showStudyButton && (
          <StudyButton
            isStudied={isStudied}
            isFirstSlide={isFirstSlide}
            onClick={onToggleStudy}
          />
        )}
      </div>
    </header>
  );
}