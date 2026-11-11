import { Check } from 'lucide-react';

interface StudyButtonProps {
  isStudied: boolean;
  isFirstSlide: boolean;
  onClick: () => void;
}

export default function StudyButton({ isStudied, isFirstSlide, onClick }: StudyButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`px-8 py-1.5 rounded-full border text-sm font-medium tracking-wide transition-all duration-200 flex items-center gap-2 cursor-pointer ${
        isStudied 
          ? 'bg-[#4E7D34] border-[#4E7D34] text-white shadow-sm' 
          : 'bg-transparent border-[#4E7D34] text-[#4E7D34] hover:bg-[#4E7D34]/10'
      }`}
    >
      {isStudied && <Check className="w-3.5 h-3.5" strokeWidth={3} />}
      {isFirstSlide ? 'start study' : 'studied'}
    </button>
  );
}