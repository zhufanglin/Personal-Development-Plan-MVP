'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAssessmentStore } from '@/store/assessmentStore';
import { LikertScale } from '@/components/assessment/LikertScale';
import {
  ASSESSMENT_LABELS, ASSESSMENT_TYPES,
  type AssessmentType,
} from '@/types/assessment';

const TYPE_MAP: Record<string, AssessmentType> = {
  holland: 'holland',
  ability: 'ability',
  values: 'values',
  'learning-habit': 'learning_habit',
  readiness: 'readiness',
};

export default function AssessmentTestPage() {
  const params = useParams();
  const router = useRouter();
  const typeSlug = params.type as string;
  const assessmentType = TYPE_MAP[typeSlug];

  const store = useAssessmentStore();
  const { currentAssessment, currentQuestions, currentIndex, answers, isLoading } = store;
  const currentQuestion = currentQuestions[currentIndex];
  const [selectedValue, setSelectedValue] = useState<number | undefined>();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!assessmentType || !ASSESSMENT_TYPES.includes(assessmentType)) {
      router.push('/assessment');
      return;
    }
    if (!currentAssessment || currentAssessment.type !== assessmentType) {
      store.startAssessment(assessmentType).catch(() => router.push('/assessment'));
    }
  }, [assessmentType]);

  useEffect(() => {
    if (currentQuestion) {
      setSelectedValue(answers[currentQuestion.id]);
    }
  }, [currentIndex, currentQuestion?.id]);

  if (!assessmentType || !currentAssessment || !currentQuestion) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-[2.5px] border-[#d2d2d7] border-t-[#2997ff] rounded-full animate-spin" />
      </div>
    );
  }

  const handleSelect = async (value: number) => {
    if (submitting) return;
    setSelectedValue(value);
    setSubmitting(true);

    try {
      await store.submitAnswer(currentAssessment.id, currentQuestion.id, value);
      store.setAnswer(currentQuestion.id, value);

      if (currentIndex < currentQuestions.length - 1) {
        store.nextQuestion();
      } else {
        const res = await store.submitAssessment(currentAssessment.id);
        router.push(`/assessment/result/${res.assessment_id}`);
      }
    } catch (err) {
      console.error('Submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePrev = () => {
    store.prevQuestion();
  };

  const label = ASSESSMENT_LABELS[assessmentType];
  const progress = (currentIndex + 1) / currentQuestions.length * 100;

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Apple glass nav */}
      <nav className="apple-glass sticky top-0 z-50">
        <div className="max-w-[680px] mx-auto px-6 h-12 flex items-center justify-between">
          <Link href="/assessment" className="text-[12px] text-[#86868b] hover:text-[#1d1d1f] transition-colors">
            ← {label}
          </Link>
          <span className="text-[12px] text-[#86868b]">
            {currentIndex + 1} / {currentQuestions.length}
          </span>
        </div>
      </nav>

      {/* Progress bar — thin Apple blue line */}
      <div className="w-full bg-[#d2d2d7]/20 h-[2px]">
        <div
          className="h-full bg-[#2997ff] transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Question area — centered, generous spacing */}
      <div className="flex-1 flex flex-col items-center justify-center max-w-[680px] mx-auto w-full px-6 py-12 sm:py-20">
        <div className="text-center mb-12 w-full">
          {currentQuestion.dimension && (
            <span className="inline-block px-3 py-1 text-[12px] font-medium rounded-full bg-[#f5f5f7] text-[#86868b] mb-5 tracking-wide">
              {currentQuestion.dimension}
            </span>
          )}
          <h2 className="text-[24px] sm:text-[32px] font-semibold tracking-tight text-[#1d1d1f] leading-snug">
            {currentQuestion.question_text}
          </h2>
        </div>

        <LikertScale
          options={currentQuestion.options}
          selectedValue={selectedValue}
          onChange={handleSelect}
          disabled={submitting}
        />

        {/* Navigation */}
        <div className="flex justify-between items-center mt-12 w-full">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="text-[15px] text-[#2997ff] disabled:text-[#d2d2d7] disabled:cursor-not-allowed hover:text-[#0077ed] transition-colors"
          >
            ← 上一题
          </button>
          {/* Progress dots — subtle indicator */}
          <div className="flex items-center gap-1.5">
            {Array.from({ length: Math.min(currentQuestions.length, 20) }, (_, i) => (
              <div
                key={i}
                className={`w-1.5 h-1.5 rounded-full transition-colors ${
                  i === currentIndex
                    ? 'bg-[#2997ff]'
                    : i < currentIndex
                    ? 'bg-[#2997ff]/30'
                    : 'bg-[#d2d2d7]/40'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
