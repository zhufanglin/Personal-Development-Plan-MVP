'use client';

interface ProgressBarProps {
  current: number;
  total: number;
  percentage?: number;
}

export function ProgressBar({ current, total, percentage }: ProgressBarProps) {
  const pct = percentage ?? (total > 0 ? ((current + 1) / total) * 100 : 0);

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        <span className="text-[12px] text-[#86868b]">
          第 {current + 1} 题 / 共 {total} 题
        </span>
        <span className="text-[12px] font-medium text-[#2997ff]">
          {Math.round(pct)}%
        </span>
      </div>
      <div className="w-full bg-[#d2d2d7]/20 rounded-full h-[3px] overflow-hidden">
        <div
          className="bg-[#2997ff] h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

