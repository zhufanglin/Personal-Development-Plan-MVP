'use client';

interface LikertScaleProps {
  options: { label: string; value: number }[];
  selectedValue?: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export function LikertScale({ options, selectedValue, onChange, disabled }: LikertScaleProps) {
  return (
    <div className="flex items-center justify-between gap-2 sm:gap-3 w-full max-w-[560px] mx-auto">
      {options.map((option) => {
        const isSelected = selectedValue === option.value;
        return (
          <button
            key={option.value}
            onClick={() => !disabled && onChange(option.value)}
            disabled={disabled}
            className={`
              flex-1 flex flex-col items-center gap-2.5 py-5 sm:py-6 rounded-2xl
              transition-all duration-300 text-center
              ${isSelected
                ? 'bg-[#1d1d1f] text-white scale-[1.03] shadow-lg shadow-black/10'
                : 'bg-[#f5f5f7] text-[#1d1d1f] hover:bg-[#e8e8ed] hover:scale-[1.01]'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <span className={`text-[12px] sm:text-[13px] font-medium leading-tight ${isSelected ? 'text-white/80' : 'text-[#86868b]'}`}>
              {option.label}
            </span>
            <span className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-[15px] sm:text-[17px] font-semibold
              transition-all duration-300
              ${isSelected
                ? 'bg-[#2997ff] text-white scale-110'
                : 'bg-[#d2d2d7]/25 text-[#86868b]'
              }`}
            >
              {option.value}
            </span>
          </button>
        );
      })}
    </div>
  );
}
