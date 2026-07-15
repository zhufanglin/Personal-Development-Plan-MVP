export type AssessmentType = 'holland' | 'ability' | 'values' | 'learning_habit' | 'readiness';
export type AssessmentStatus = 'not_started' | 'in_progress' | 'completed';

export interface Option {
  label: string;
  value: number;
}

export interface AssessmentQuestion {
  id: string;
  type: AssessmentType;
  dimension?: string;
  question_text: string;
  options: Option[];
  sort_order: number;
}

export interface Assessment {
  id: string;
  type: AssessmentType;
  status: AssessmentStatus;
  current_question: number;
  total_questions: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface AssessmentResult {
  id: string;
  type: string;
  result_data: Record<string, number | string>;
  summary?: string;
  created_at: string;
}

export interface AssessmentHistory {
  id: string;
  type: string;
  result_snapshot: Record<string, number | string>;
  version: number;
  created_at: string;
}

export interface StartAssessmentResponse {
  assessment: Assessment;
  questions: AssessmentQuestion[];
}

export interface SubmitAnswerResponse {
  question_id: string;
  current_question: number;
  total_questions: number;
  is_last: boolean;
}

export interface SubmitResponse {
  assessment_id: string;
  result: AssessmentResult;
  message: string;
}

export interface AssessmentStatusMap {
  holland: Assessment | null;
  ability: Assessment | null;
  values: Assessment | null;
  learning_habit: Assessment | null;
  readiness: Assessment | null;
}

export const ASSESSMENT_TYPES: AssessmentType[] = [
  'holland', 'ability', 'values', 'learning_habit', 'readiness'
];

export const ASSESSMENT_LABELS: Record<AssessmentType, string> = {
  holland: '霍兰德兴趣测评',
  ability: '能力自评',
  values: '职业价值观测评',
  learning_habit: '学习习惯测评',
  readiness: '准备度测评',
};

export const ASSESSMENT_DESCRIPTIONS: Record<AssessmentType, string> = {
  holland: '探索你的职业兴趣类型，找到最适合的发展方向',
  ability: '评估你在学习、沟通、协作等多维度的能力水平',
  values: '了解你内心最看重的职业价值观',
  learning_habit: '分析你的学习习惯，发现改进空间',
  readiness: '评估你对未来职业或深造的准备程度',
};

export const ASSESSMENT_ICONS: Record<AssessmentType, string> = {
  holland: '🧭',
  ability: '💪',
  values: '⭐',
  learning_habit: '📚',
  readiness: '🎯',
};
