'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAssessmentStore } from '@/store/assessmentStore';
import type { AssessmentType } from '@/types/assessment';

export function useAssessment() {
  const router = useRouter();
  const store = useAssessmentStore();

  useEffect(() => {
    store.fetchStatus();
  }, []);

  const handleStart = async (type: AssessmentType) => {
    try {
      await store.startAssessment(type);
      router.push(`/assessment/${type}`);
    } catch (err) {
      console.error('Failed to start assessment:', err);
    }
  };

  return {
    ...store,
    handleStart,
  };
}

export function useAssessmentType(type: AssessmentType) {
  const router = useRouter();
  const store = useAssessmentStore();

  useEffect(() => {
    if (!store.currentAssessment) {
      store.startAssessment(type).catch(() => {
        router.push('/assessment');
      });
    }
  }, [type]);

  const currentQuestion = store.currentQuestions[store.currentIndex];
  const progress = store.currentQuestions.length > 0
    ? ((store.currentIndex + 1) / store.currentQuestions.length) * 100
    : 0;

  const handleAnswer = async (value: number) => {
    if (!store.currentAssessment || !currentQuestion) return;

    store.setAnswer(currentQuestion.id, value);

    await store.submitAnswer(
      store.currentAssessment.id,
      currentQuestion.id,
      value
    );

    if (store.currentIndex < store.currentQuestions.length - 1) {
      store.nextQuestion();
    }
  };

  const handleSubmit = async () => {
    if (!store.currentAssessment) return;
    try {
      const res = await store.submitAssessment(store.currentAssessment.id);
      router.push(`/assessment/result/${res.assessment_id}`);
    } catch (err) {
      console.error('Failed to submit:', err);
    }
  };

  return {
    ...store,
    currentQuestion,
    progress,
    handleAnswer,
    handleSubmit,
  };
}
