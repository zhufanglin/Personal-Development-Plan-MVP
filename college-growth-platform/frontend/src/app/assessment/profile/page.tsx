'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAssessmentStore } from '@/store/assessmentStore';
import { ResultRadar } from '@/components/assessment/ResultRadar';
import {
  ASSESSMENT_LABELS, ASSESSMENT_ICONS,
  type AssessmentType,
} from '@/types/assessment';

const TYPE_ORDER: AssessmentType[] = ['holland', 'ability', 'values', 'learning_habit', 'readiness'];

function getScoreLabel(score: number) {
  if (score >= 80) return '优秀';
  if (score >= 60) return '良好';
  if (score >= 40) return '一般';
  return '待提升';
}

function getScoreBarColor(score: number) {
  if (score >= 80) return 'bg-[#30d158]';
  if (score >= 60) return 'bg-[#2997ff]';
  if (score >= 40) return 'bg-[#ff9f0a]';
  return 'bg-[#ff453a]';
}

function ChevronRight() {
  return (
    <svg width="7" height="12" viewBox="0 0 7 12" fill="none" className="ml-1">
      <path d="M1 1l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function AssessmentSection({ type, data, index }: { type: AssessmentType; data: any; index: number }) {
  const rd = data.result_data;
  const icon = ASSESSMENT_ICONS[type];
  const label = ASSESSMENT_LABELS[type];
  const isDark = index % 2 === 0;

  const excludeKeys = ['holland_code', 'holland_description'];
  const radarData = Object.entries(rd)
    .filter(([key]) => !excludeKeys.includes(key) && typeof rd[key] === 'number')
    .map(([dimension, score]) => ({
      dimension,
      score: typeof score === 'number' ? score : 0,
      fullMark: 100,
    }));

  const sortedDims = radarData.sort((a, b) => b.score - a.score);
  const topDims = sortedDims.slice(0, 3);

  return (
    <section className={`${isDark ? 'bg-[#000] text-white' : 'bg-[#f5f5f7] text-[#1d1d1f]'} py-20 sm:py-28`}>
      <div className="max-w-[980px] mx-auto px-6">
        <div className="text-center mb-12">
          <span className="text-[48px] mb-4 block">{icon}</span>
          <h2 className="section-headline">{label}</h2>
          {type === 'holland' && typeof rd.holland_code === 'string' && (
            <p className="text-[#2997ff] text-[19px] mt-3 font-medium">
              霍兰德代码：{rd.holland_code as string}
            </p>
          )}
        </div>

        <div className="grid sm:grid-cols-2 gap-8 items-start">
          {/* Radar Chart */}
          {radarData.length > 2 && (
            <div className="flex justify-center">
              <div className={`${isDark ? 'bg-[#1d1d1f]' : 'bg-white'} rounded-[20px] p-8 w-full`}>
                <ResultRadar data={radarData} dark={isDark} />
              </div>
            </div>
          )}

          {/* Top Dimensions + Summary */}
          <div>
            <div className={`${isDark ? 'bg-[#1d1d1f]' : 'bg-white'} rounded-[20px] p-8`}>
              <h3 className="text-[13px] font-medium text-[#86868b] mb-5 uppercase tracking-widest">
                突出维度
              </h3>
              <div className="flex flex-wrap gap-2 mb-8">
                {topDims.map((d) => (
                  <span
                    key={d.dimension}
                    className={`px-4 py-2 text-[15px] font-medium rounded-full ${isDark ? 'bg-[#2d2d2f] text-white' : 'bg-[#f5f5f7] text-[#1d1d1f]'}`}
                  >
                    {d.dimension} · {Math.round(d.score)}
                  </span>
                ))}
              </div>

              {data.summary && (
                <div>
                  <h3 className="text-[13px] font-medium text-[#86868b] mb-4 uppercase tracking-widest">
                    评估总结
                  </h3>
                  <p className={`text-[17px] leading-relaxed ${isDark ? 'text-[#f5f5f7]' : 'text-[#1d1d1f]'}`}>
                    {data.summary}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function GrowthProfilePage() {
  const { fetchGrowthProfile, growthProfile, isLoading } = useAssessmentStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchGrowthProfile().catch((err) => {
      setError(err?.message || '获取成长画像失败');
    });
  }, []);

  if (isLoading && !growthProfile) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-[2.5px] border-[#d2d2d7] border-t-[#2997ff] rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !growthProfile) {
    return (
      <div className="max-w-[600px] mx-auto px-6 py-20 text-center">
        <p className="text-[#ff453a] text-[17px] mb-6">{error || '加载失败'}</p>
        <Link href="/assessment" className="apple-cta">返回测评中心 <ChevronRight /></Link>
      </div>
    );
  }

  const { completed_count, total_count, assessments, overall_scores, overall_avg } = growthProfile;
  const allCompleted = completed_count === total_count;
  const suggestions = growthProfile.suggestions;

  return (
    <div className="min-h-screen">
      {/* ── Hero — dark full-bleed ── */}
      <section className="relative bg-[#000] text-white overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(41,151,255,0.08)_0%,transparent_60%)]" />
        <div className="relative max-w-[980px] mx-auto px-6 py-20 sm:py-28 text-center">
          <h1 className="section-headline text-white animate-apple-fade">
            我的成长画像
          </h1>
          <p className="section-subline !text-[#86868b] mt-4 animate-apple-fade-delay">
            {allCompleted
              ? '恭喜你完成了全部测评。'
              : `已完成 ${completed_count}/${total_count} 项测评。`}
          </p>

          {/* Score overview cards */}
          <div className="grid grid-cols-3 gap-4 mt-12 max-w-[640px] mx-auto animate-apple-fade-delay-2">
            <div className="bg-[#1d1d1f] rounded-[16px] p-6 text-left">
              <p className="text-[#86868b] text-[12px] uppercase tracking-widest">综合得分</p>
              <p className="text-[48px] font-semibold mt-2 tracking-tight leading-none">{Math.round(overall_avg)}</p>
              <p className="text-[#86868b] text-[13px] mt-2">{getScoreLabel(overall_avg)}</p>
            </div>
            <div className="bg-[#1d1d1f] rounded-[16px] p-6 text-left">
              <p className="text-[#86868b] text-[12px] uppercase tracking-widest">完成测评</p>
              <p className="text-[48px] font-semibold mt-2 tracking-tight leading-none">
                {completed_count}<span className="text-[24px] text-[#86868b]">/{total_count}</span>
              </p>
              <p className="text-[#86868b] text-[13px] mt-2">项</p>
            </div>
            <div className="bg-[#1d1d1f] rounded-[16px] p-6 text-left">
              <p className="text-[#86868b] text-[12px] uppercase tracking-widest mb-3">各项得分</p>
              <div className="space-y-2">
                {Object.entries(overall_scores).map(([type, score]) => (
                  <div key={type} className="flex items-center justify-between text-[12px]">
                    <span className="text-[#86868b]">{ASSESSMENT_LABELS[type as AssessmentType] || type}</span>
                    <span className="text-white font-medium">{Math.round(score as number)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Score Bars — light section ── */}
      {Object.keys(overall_scores).length > 0 && (
        <section className="bg-[#f5f5f7] py-20 sm:py-28">
          <div className="max-w-[640px] mx-auto px-6">
            <h2 className="section-headline text-[#1d1d1f] text-center mb-12">
              各测评综合得分
            </h2>
            <div className="space-y-8">
              {TYPE_ORDER.filter(t => overall_scores[t] !== undefined).map((type) => {
                const score = overall_scores[type];
                return (
                  <div key={type}>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[17px] text-[#1d1d1f] flex items-center gap-2.5">
                        <span className="text-xl">{ASSESSMENT_ICONS[type]}</span>
                        {ASSESSMENT_LABELS[type]}
                      </span>
                      <span className="text-[19px] font-semibold text-[#1d1d1f]">{Math.round(score)}</span>
                    </div>
                    <div className="w-full bg-[#d2d2d7]/30 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${getScoreBarColor(score)} transition-all duration-700`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* ── Individual Assessment Sections ── */}
      {TYPE_ORDER.filter(t => assessments[t]).map((type, i) => (
        <AssessmentSection key={type} type={type} data={assessments[type]} index={i} />
      ))}

      {/* ── Growth Suggestions ── */}
      {suggestions && (
        <>
          {/* Suggestions Hero */}
          <section className="relative bg-[#000] text-white overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_100%,rgba(48,209,88,0.08)_0%,transparent_60%)]" />
            <div className="relative py-20 sm:py-28 text-center">
              <h2 className="section-headline text-white">
                成长建议
              </h2>
              <p className="section-subline !text-[#86868b] mt-4">
                基于五项测评结果，为你量身定制。
              </p>
            </div>
          </section>

          {/* Strengths */}
          {suggestions.strengths.length > 0 && (
            <section className="bg-[#f5f5f7] py-16 sm:py-24">
              <div className="max-w-[640px] mx-auto px-6">
                <h3 className="section-headline text-[#1d1d1f] text-center mb-10 !text-[32px] sm:!text-[40px]">
                  优势亮点
                </h3>
                <div className="space-y-4">
                  {suggestions.strengths.map((item, idx) => (
                    <div key={idx} className="bg-white rounded-[16px] p-6 flex items-start gap-4">
                      <span className="text-2xl flex-shrink-0">{item.icon}</span>
                      <p className="text-[17px] text-[#1d1d1f] leading-relaxed">{item.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Cross Analysis */}
          {suggestions.cross_analysis.length > 0 && (
            <section className="bg-white py-16 sm:py-24">
              <div className="max-w-[640px] mx-auto px-6">
                <h3 className="section-headline text-[#1d1d1f] text-center mb-10 !text-[32px] sm:!text-[40px]">
                  交叉洞察
                </h3>
                <div className="space-y-4">
                  {suggestions.cross_analysis.map((item, idx) => (
                    <div key={idx} className="bg-[#f5f5f7] rounded-[16px] p-6 flex items-start gap-4">
                      <span className="text-2xl flex-shrink-0">{item.icon}</span>
                      <p className="text-[17px] text-[#1d1d1f] leading-relaxed">{item.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Career */}
          {suggestions.career.length > 0 && (
            <section className="bg-[#f5f5f7] py-16 sm:py-24">
              <div className="max-w-[640px] mx-auto px-6">
                <h3 className="section-headline text-[#1d1d1f] text-center mb-10 !text-[32px] sm:!text-[40px]">
                  职业方向
                </h3>
                <div className="space-y-4">
                  {suggestions.career.map((item, idx) => (
                    <div key={idx} className="bg-white rounded-[16px] p-6 flex items-start gap-4">
                      <span className="text-2xl flex-shrink-0">{item.icon}</span>
                      <p className="text-[17px] text-[#1d1d1f] leading-relaxed">{item.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Improvements */}
          {suggestions.improvements.length > 0 && (
            <section className="bg-white py-16 sm:py-24">
              <div className="max-w-[640px] mx-auto px-6">
                <h3 className="section-headline text-[#1d1d1f] text-center mb-10 !text-[32px] sm:!text-[40px]">
                  待提升领域
                </h3>
                <div className="space-y-4">
                  {suggestions.improvements.map((item, idx) => (
                    <div key={idx} className="bg-[#f5f5f7] rounded-[16px] p-6">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-xl">{item.icon}</span>
                        {item.dimension && (
                          <span className="text-[19px] font-medium text-[#1d1d1f]">{item.dimension}</span>
                        )}
                        {item.score !== undefined && (
                          <span className="text-[15px] text-[#86868b]">{item.score}分</span>
                        )}
                      </div>
                      <p className="text-[17px] text-[#1d1d1f] leading-relaxed">{item.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Action Plan */}
          {suggestions.action_plan.length > 0 && (
            <section className="bg-[#000] text-white py-16 sm:py-24">
              <div className="max-w-[640px] mx-auto px-6">
                <h3 className="section-headline text-center mb-10 !text-[32px] sm:!text-[40px]">
                  行动计划
                </h3>
                <div className="space-y-4">
                  {suggestions.action_plan.map((item, idx) => (
                    <div key={idx} className="bg-[#1d1d1f] rounded-[16px] p-6 flex items-start gap-4">
                      <span className="text-2xl flex-shrink-0">{item.icon}</span>
                      <div className="flex-1">
                        {item.priority && (
                          <span className={`inline-block px-3 py-1 text-[12px] font-medium rounded-full mb-3 tracking-wide ${
                            item.priority === '高' ? 'bg-[#ff453a]/20 text-[#ff453a]' :
                            item.priority === '中' ? 'bg-[#ff9f0a]/20 text-[#ff9f0a]' :
                            'bg-[#2997ff]/20 text-[#2997ff]'
                          }`}>
                            {item.priority}
                          </span>
                        )}
                        <p className="text-[17px] text-[#f5f5f7] leading-relaxed">{item.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}
        </>
      )}

      {/* ── Not completed ── */}
      {!allCompleted && (
        <section className="bg-[#f5f5f7] py-20 sm:py-28 text-center">
          <h2 className="section-headline text-[#1d1d1f]">
            继续你的测评之旅
          </h2>
          <p className="section-subline mt-3">
            还有 {total_count - completed_count} 项测评未完成
          </p>
          <div className="mt-8">
            <Link href="/assessment" className="apple-btn-primary">
              继续测评
            </Link>
          </div>
        </section>
      )}

      {/* ── Back ── */}
      <section className="bg-white py-12 text-center">
        <Link href="/assessment" className="apple-cta">
          返回测评中心 <ChevronRight />
        </Link>
      </section>
    </div>
  );
}
