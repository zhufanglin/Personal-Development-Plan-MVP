import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type {
  AssessmentType, AssessmentStatusMap, Assessment,
  AssessmentQuestion, AssessmentResult,
  StartAssessmentResponse, SubmitAnswerResponse, SubmitResponse,
} from '@/types/assessment';

interface SuggestionItem {
  source?: string;
  icon: string;
  text: string;
  dimension?: string;
  score?: number;
  priority?: string;
}

interface GrowthSuggestions {
  strengths: SuggestionItem[];
  improvements: SuggestionItem[];
  career: SuggestionItem[];
  action_plan: SuggestionItem[];
  cross_analysis: SuggestionItem[];
}

interface GrowthProfile {
  completed_count: number;
  total_count: number;
  assessments: Record<string, {
    id: string;
    type: string;
    result_data: Record<string, number | string>;
    summary?: string;
    completed_at?: string;
  }>;
  overall_scores: Record<string, number>;
  overall_avg: number;
  suggestions: GrowthSuggestions;
}

interface AssessmentState {
  statusMap: AssessmentStatusMap;
  currentAssessment: Assessment | null;
  currentQuestions: AssessmentQuestion[];
  currentIndex: number;
  answers: Record<string, number>;
  result: AssessmentResult | null;
  isLoading: boolean;
  error: string | null;

  fetchStatus: () => Promise<void>;
  startAssessment: (type: AssessmentType) => Promise<StartAssessmentResponse>;
  fetchQuestions: (type: AssessmentType) => Promise<AssessmentQuestion[]>;
  submitAnswer: (assessmentId: string, questionId: string, value: number) => Promise<SubmitAnswerResponse>;
  submitAssessment: (assessmentId: string) => Promise<SubmitResponse>;
  fetchResult: (assessmentId: string) => Promise<AssessmentResult>;
  fetchGrowthProfile: () => Promise<GrowthProfile>;
  growthProfile: GrowthProfile | null;
  setAnswer: (questionId: string, value: number) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  resetCurrent: () => void;
}

export const useAssessmentStore = create<AssessmentState>((set, get) => ({
  statusMap: {
    holland: null, ability: null, values: null,
    learning_habit: null, readiness: null,
  },
  currentAssessment: null,
  currentQuestions: [],
  currentIndex: 0,
  answers: {},
  result: null,
  growthProfile: null,
  isLoading: false,
  error: null,

  fetchStatus: async () => {
    set({ isLoading: true, error: null });
    try {
      const res: any = await apiService.get('/assessments');
      set({ statusMap: res, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || '获取测评状态失败', isLoading: false });
    }
  },

  startAssessment: async (type) => {
    set({ isLoading: true, error: null });
    try {
      const res: any = await apiService.post(`/assessments/${type}/start`);
      const data = res as StartAssessmentResponse;
      set({
        currentAssessment: data.assessment,
        currentQuestions: data.questions,
        currentIndex: 0,
        answers: {},
        isLoading: false,
      });
      return data;
    } catch (err: any) {
      set({ error: err.message || '开始测评失败', isLoading: false });
      throw err;
    }
  },

  fetchQuestions: async (type) => {
    set({ isLoading: true, error: null });
    try {
      const res: any = await apiService.get(`/assessments/${type}/questions`);
      set({ currentQuestions: res.questions, isLoading: false });
      return res.questions;
    } catch (err: any) {
      set({ error: err.message || '获取题目失败', isLoading: false });
      throw err;
    }
  },

  submitAnswer: async (assessmentId, questionId, value) => {
    try {
      const res: any = await apiService.post(`/assessments/${assessmentId}/answer`, {
        question_id: questionId,
        answer_value: { value },
      });
      return res as SubmitAnswerResponse;
    } catch (err: any) {
      set({ error: err.message || '提交答案失败' });
      throw err;
    }
  },

  submitAssessment: async (assessmentId) => {
    set({ isLoading: true, error: null });
    try {
      const res: any = await apiService.post(`/assessments/${assessmentId}/submit`);
      const data = res as SubmitResponse;
      set({
        result: data.result,
        currentAssessment: null,
        currentQuestions: [],
        isLoading: false,
      });
      return data;
    } catch (err: any) {
      set({ error: err.message || '提交测评失败', isLoading: false });
      throw err;
    }
  },

  fetchResult: async (assessmentId) => {
    set({ isLoading: true, error: null });
    try {
      const res: any = await apiService.get(`/assessments/${assessmentId}/result`);
      set({ result: res as AssessmentResult, isLoading: false });
      return res as AssessmentResult;
    } catch (err: any) {
      set({ error: err.message || '获取结果失败', isLoading: false });
      throw err;
    }
  },

  fetchGrowthProfile: async () => {
    set({ isLoading: true, error: null });
    try {
      const res: any = await apiService.get('/assessments/growth-profile');
      set({ growthProfile: res as GrowthProfile, isLoading: false });
      return res as GrowthProfile;
    } catch (err: any) {
      set({ error: err.message || '获取成长画像失败', isLoading: false });
      throw err;
    }
  },

  setAnswer: (questionId, value) => {
    set((state) => ({
      answers: { ...state.answers, [questionId]: value },
    }));
  },

  nextQuestion: () => {
    set((state) => ({
      currentIndex: Math.min(state.currentIndex + 1, state.currentQuestions.length - 1),
    }));
  },

  prevQuestion: () => {
    set((state) => ({
      currentIndex: Math.max(state.currentIndex - 1, 0),
    }));
  },

  resetCurrent: () => {
    set({
      currentAssessment: null,
      currentQuestions: [],
      currentIndex: 0,
      answers: {},
      result: null,
    });
  },
}));
