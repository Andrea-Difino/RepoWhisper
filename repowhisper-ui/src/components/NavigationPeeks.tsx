import { Lock } from 'lucide-react';

interface NavigationPeeksProps {
  canGoPrev: boolean;
  canGoNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  isLastSlide: boolean;
}

export default function NavigationPeeks({ 
  canGoPrev, 
  canGoNext, 
  onPrev, 
  onNext, 
  isLastSlide 
}: NavigationPeeksProps) {
  return (
    <>
      <div
        onClick={onPrev}
        className={`fixed left-0 top-1/2 -translate-y-1/2 w-11.5 xl:w-16.25 h-[45vh] bg-[#787C82] rounded-r-[36px] transition-all duration-500 z-20 ${
          canGoPrev
            ? 'opacity-90 hover:w-17.5 cursor-pointer'
            : 'opacity-0 pointer-events-none -translate-x-full'
        }`}
        title={canGoPrev ? "Torna al modulo precedente" : ""}
      />

      <div
        onClick={onNext}
        className={`fixed right-0 top-1/2 -translate-y-1/2 w-11.5 xl:w-16.25 h-[45vh] bg-[#EFEFEF] rounded-l-[36px] transition-all duration-500 z-20 flex items-center justify-center ${
          !isLastSlide 
            ? canGoNext 
              ? 'opacity-100 hover:w-17.5 cursor-pointer shadow-md' 
              : 'opacity-50 cursor-not-allowed' 
            : 'opacity-0 pointer-events-none translate-x-full'
        }`}
        title={canGoNext ? "Go to the next module" : "Complete this module first clicking on 'studied'"}
      >
        {!canGoNext && !isLastSlide && <Lock className="w-4 h-4 text-black/25" />}
      </div>
    </>
  );
}