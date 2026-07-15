'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAssessmentStore } from '@/store/assessmentStore';
import { ResultRadar } from '@/components/assessment/ResultRadar';
import { ASSESSMENT_LABELS, type AssessmentType } from '@/types/assessment';

const URL_SLUG: Record<string, string> = {
  holland: 'holland',
  ability: 'ability',
  values: 'values',
  learning_habit: 'learning-habit',
  readiness: 'readiness',
};

function ChevronRight() {
  return (
    <svg width="7" height="12" viewBox="0 0 7 12" fill="none" className="ml-1">
      <path d="M1 1l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function AssessmentResultPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params.id as string;
  const { fetchResult, result, isLoading } = useAssessmentStore();
  const [error, setError] = useState<string | null>(null);
  const [isRedoing, setIsRedoing] = useState(false);

  const handleRedo = () => {
    if (!result) return;
    const slug = URL_SLUG[result.type] || result.type;
    setIsRedoing(true);
    router.push(`/assessment/${slug}`);
  };

  useEffect(() => {
    if (assessmentId) {
      fetchResult(assessmentId).catch((err) => {
        setError(err?.message || '获取结果失败');
      });
    }
  }, [assessmentId]);

  if (isLoading && !result) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-[2.5px] border-[#d2d2d7] border-t-[#2997ff] rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-[600px] mx-auto px-6 py-20 text-center">
        <p className="text-[#ff453a] text-[17px] mb-6">{error || '未找到测评结果'}</p>
        <Link href="/assessment" className="apple-cta">返回测评中心 <ChevronRight /></Link>
      </div>
    );
  }

  const radarData = Object.entries(result.result_data)
    .filter(([key]) => !['holland_code', 'holland_description'].includes(key))
    .map(([dimension, score]) => ({
      dimension,
      score: typeof score === 'number' ? score : 0,
      fullMark: 100,
    }));

  const typeLabel = ASSESSMENT_LABELS[result.type as AssessmentType] || result.type;
  const hasHollandCode = typeof result.result_data.holland_code === 'string';

  return (
    <div className="min-h-screen">
      {/* ── Hero — dark full-bleed ── */}
      <section className="relative bg-[#000] text-white overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(41,151,255,0.1)_0%,transparent_60%)]" />
        <div className="relative max-w-[980px] mx-auto px-6 py-20 sm:py-28 text-center">
          <p className="text-[#86868b] text-[15px] mb-2 animate-apple-fade">{typeLabel}</p>
          <h1 className="section-headline text-white animate-apple-fade">
            测评结果
          </h1>

          {hasHollandCode && (
            <div className="mt-10 animate-apple-fade-delay">
              <p className="text-[#86868b] text-[15px] mb-3">你的霍兰德代码</p>
              <p className="text-[64px] sm:text-[80px] font-semibold tracking-tight text-[#2997ff] leading-none">
                {result.result_data.holland_code as string}
              </p>
              {typeof result.result_data.holland_description === 'string' && (
                <p className="text-[#86868b] text-[17px] mt-4 max-w-[500px] mx-auto leading-relaxed">
                  {result.result_data.holland_description as string}
                </p>
              )}
            </div>
          )}
        </div>
      </section>

      {/* ── Radar Chart — light section ── */}
      {radarData.length > 0 && (
        <section className="bg-[#f5f5f7] py-16 sm:py-24">
          <div className="max-w-[680px] mx-auto px-6">
            <div className="bg-white rounded-[20px] p-8 sm:p-10">
              <ResultRadar data={radarData} />
            </div>
          </div>
        </section>
      )}

      {/* ── Summary — white section ── */}
      {result.summary && (
        <section className="bg-white py-16 sm:py-24">
          <div className="max-w-[680px] mx-auto px-6">
            <h2 className="section-headline text-[#1d1d1f] text-center mb-8">
              综合评估
            </h2>
            <div className="bg-[#f5f5f7] rounded-[20px] p-8 sm:p-10">
              <p className="text-[19px] text-[#1d1d1f] leading-relaxed">{result.summary}</p>
            </div>
          </div>
        </section>
      )}

      {/* ── Actions — Apple-style CTA section ── */}
      <section className="bg-[#f5f5f7] py-16 sm:py-20">
        <div className="max-w-[680px] mx-auto px-6">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/assessment" className="apple-btn-primary">
              返回测评中心
            </Link>
            <button
              onClick={handleRedo}
              disabled={isRedoing}
              className="apple-btn-secondary disabled:opacity-40"
            >
              {isRedoing ? '正在重做...' : '重新测评'}
            </button>
          </div>
          <div className="text-center mt-6">
            <Link href="/assessment/profile" className="apple-cta">
              查看成长画像 <ChevronRight />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
