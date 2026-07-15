'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAssessmentStore } from '@/store/assessmentStore';
import {
  ASSESSMENT_LABELS, ASSESSMENT_DESCRIPTIONS, ASSESSMENT_ICONS,
  type AssessmentType, type Assessment,
} from '@/types/assessment';

const URL_SLUG: Record<AssessmentType, string> = {
  holland: 'holland',
  ability: 'ability',
  values: 'values',
  learning_habit: 'learning-habit',
  readiness: 'readiness',
};

/* Each card gets a unique gradient — like Apple product tiles */
const CARD_VISUALS: Record<AssessmentType, { gradient: string; emoji: string }> = {
  holland: {
    gradient: 'from-[#1a1a2e] via-[#16213e] to-[#0f3460]',
    emoji: '🧭',
  },
  ability: {
    gradient: 'from-[#1a1a1a] via-[#2d2d2d] to-[#3a3a3a]',
    emoji: '💡',
  },
  values: {
    gradient: 'from-[#0c0c1d] via-[#1a0a2e] to-[#2d1b4e]',
    emoji: '⚖️',
  },
  learning_habit: {
    gradient: 'from-[#0a1628] via-[#0f2847] to-[#1a3a5c]',
    emoji: '📚',
  },
  readiness: {
    gradient: 'from-[#1a0a0a] via-[#2e1515] to-[#4a1a1a]',
    emoji: '🚀',
  },
};

function ChevronRight() {
  return (
    <svg width="7" height="12" viewBox="0 0 7 12" fill="none" className="ml-1">
      <path d="M1 1l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function AssessmentCard({ type, assessment, index }: { type: AssessmentType; assessment: Assessment | null; index: number }) {
  const router = useRouter();
  const label = ASSESSMENT_LABELS[type];
  const desc = ASSESSMENT_DESCRIPTIONS[type];
  const visual = CARD_VISUALS[type];

  const statusText = !assessment ? '未开始' : assessment.status === 'in_progress' ? '进行中' : '已完成';
  const statusDot = !assessment ? 'bg-[#86868b]' : assessment.status === 'in_progress' ? 'bg-[#ff9f0a]' : 'bg-[#30d158]';

  const handleClick = () => {
    router.push(`/assessment/${URL_SLUG[type]}`);
  };

  const isCompleted = assessment?.status === 'completed' && !!assessment.id;

  return (
    <div
      className="group relative rounded-[20px] overflow-hidden animate-apple-scale cursor-pointer"
      style={{ animationDelay: `${index * 0.1}s` }}
      onClick={handleClick}
    >
      {/* Gradient visual area — Apple product image zone */}
      <div className={`bg-gradient-to-br ${visual.gradient} px-8 pt-10 pb-8 flex flex-col items-center justify-center min-h-[260px]`}>
        <span className="text-[64px] mb-4 drop-shadow-lg group-hover:scale-110 transition-transform duration-500">
          {visual.emoji}
        </span>
        <h3 className="text-white text-[28px] sm:text-[32px] font-semibold tracking-tight text-center leading-tight">
          {label}
        </h3>
        <p className="text-white/50 text-[15px] mt-2 text-center max-w-[260px] leading-snug">
          {desc}
        </p>
      </div>

      {/* Bottom info bar */}
      <div className="bg-[#f5f5f7] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${statusDot}`} />
          <span className="text-[13px] text-[#86868b]">{statusText}</span>
        </div>

        {isCompleted ? (
          <div className="flex items-center gap-3">
            <Link
              href={`/assessment/result/${assessment.id}`}
              className="apple-cta text-[14px] !text-[#2997ff]"
              onClick={(e) => e.stopPropagation()}
            >
              查看结果 <ChevronRight />
            </Link>
            <button
              onClick={(e) => { e.stopPropagation(); handleClick(); }}
              className="apple-cta text-[14px] !text-[#86868b] hover:!text-[#1d1d1f]"
            >
              重做
            </button>
          </div>
        ) : (
          <span className="apple-cta text-[14px] pointer-events-none">
            {!assessment || assessment.status === 'not_started' ? '开始测评' : '继续答题'} <ChevronRight />
          </span>
        )}
      </div>
    </div>
  );
}

export default function AssessmentCenterPage() {
  const { statusMap, fetchStatus, isLoading } = useAssessmentStore();

  useEffect(() => {
    fetchStatus();
  }, []);

  const types: AssessmentType[] = ['holland', 'ability', 'values', 'learning_habit', 'readiness'];
  const completedCount = types.filter(t => statusMap[t]?.status === 'completed').length;
  const allCompleted = completedCount === types.length;

  return (
    <div>
      {/* ── Hero — full-bleed dark with gradient ── */}
      <section className="relative bg-[#000] text-white overflow-hidden">
        {/* Subtle radial gradient overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(41,151,255,0.12)_0%,transparent_60%)]" />
        <div className="relative max-w-[980px] mx-auto px-6 py-24 sm:py-32 text-center">
          <h1 className="section-headline text-white animate-apple-fade">
            智能测评中心
          </h1>
          <p className="section-subline !text-[#86868b] mt-4 max-w-[520px] mx-auto animate-apple-fade-delay">
            完成五项专业测评，发现自我，规划未来。
          </p>
          {completedCount > 0 && (
            <div className="mt-8 animate-apple-fade-delay-2">
              <Link
                href="/assessment/profile"
                className="apple-cta inline-flex items-center"
              >
                {allCompleted ? '查看成长画像' : `成长画像 (${completedCount}/${types.length})`}
                <ChevronRight />
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* ── Assessment Cards — Apple product grid ── */}
      <section className="max-w-[980px] mx-auto px-6 py-12 sm:py-16">
        {isLoading && !statusMap.holland ? (
          <div className="flex justify-center py-24">
            <div className="w-8 h-8 border-[2.5px] border-[#d2d2d7] border-t-[#2997ff] rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2">
            {types.map((type, i) => (
              <AssessmentCard key={type} type={type} assessment={statusMap[type]} index={i} />
            ))}
          </div>
        )}
      </section>

      {/* ── Bottom CTA — Apple-style light section ── */}
      {completedCount > 0 && !allCompleted && (
        <section className="bg-[#f5f5f7] py-20 sm:py-28 text-center">
          <h2 className="section-headline text-[#1d1d1f]">
            你的成长画像
          </h2>
          <p className="section-subline mt-3">
            已完成 {completedCount}/{types.length} 项测评
          </p>
          <div className="mt-8">
            <Link href="/assessment/profile" className="apple-btn-primary">
              查看画像
            </Link>
          </div>
        </section>
      )}

      {/* ── All completed — celebration CTA ── */}
      {allCompleted && (
        <section className="relative bg-[#000] text-white overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_100%,rgba(48,209,88,0.1)_0%,transparent_60%)]" />
          <div className="relative max-w-[980px] mx-auto px-6 py-20 sm:py-28 text-center">
            <h2 className="section-headline text-white">
              恭喜你，已完成全部测评
            </h2>
            <p className="section-subline !text-[#86868b] mt-3">
              查看你的专属成长画像与个性化建议
            </p>
            <div className="mt-8 flex items-center justify-center gap-4">
              <Link href="/assessment/profile" className="apple-btn-primary">
                查看成长画像
              </Link>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
