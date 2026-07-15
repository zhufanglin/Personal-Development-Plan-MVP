from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.assessment import (
    Assessment, AssessmentQuestion, AssessmentResponse,
    AssessmentResult, AssessmentHistory
)
from app.services.ai_service import ai_service

ASSESSMENT_TYPES = ["holland", "ability", "values", "learning_habit", "readiness"]

HOLLAND_DIMENSIONS = {
    "R": "现实型(Realistic)",
    "I": "研究型(Investigative)",
    "A": "艺术型(Artistic)",
    "S": "社会型(Social)",
    "E": "企业型(Enterprising)",
    "C": "常规型(Conventional)"
}

ABILITY_DIMENSIONS = [
    "学习能力", "沟通能力", "团队协作", "问题解决",
    "创新思维", "领导力", "时间管理", "抗压能力"
]

VALUES_DIMENSIONS = [
    "成就感", "安全感", "创造力", "人际关系",
    "经济报酬", "社会贡献", "工作环境", "个人成长"
]

LEARNING_HABIT_DIMENSIONS = [
    "学习计划", "专注力", "复习习惯", "知识整理",
    "主动学习", "时间分配", "学习环境", "自我评估"
]

READINESS_DIMENSIONS = [
    "自我认知", "职业了解", "技能准备", "心理准备",
    "信息获取", "决策能力", "行动规划", "资源利用"
]

DEFAULT_QUESTIONS = {
    "holland": [
        {"dimension": "R", "text": "我喜欢动手修理或组装物品", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "R", "text": "我对机械或电子设备的工作原理感到好奇", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "R", "text": "我喜欢户外活动和体力工作", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "I", "text": "我喜欢探索事物的规律和原理", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "I", "text": "我享受解决复杂的智力问题", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "I", "text": "我喜欢独立进行研究和分析", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "A", "text": "我有丰富的想象力和创造力", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "A", "text": "我喜欢从事艺术创作或表达", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "A", "text": "我重视美感和自我表达", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "S", "text": "我乐于帮助他人解决问题", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "S", "text": "我喜欢与他人合作完成工作", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "S", "text": "我关心他人的感受和需求", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "E", "text": "我善于说服他人接受我的观点", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "E", "text": "我喜欢领导和组织团队活动", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "E", "text": "我勇于承担风险和挑战", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "C", "text": "我喜欢按照规则和流程办事", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "C", "text": "我注重工作的准确性和条理性", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "C", "text": "我喜欢处理数据和文书工作", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
    ],
    "ability": [
        {"dimension": "学习能力", "text": "我能快速掌握新的知识和技能", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "学习能力", "text": "我善于从多个渠道获取学习资源", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "沟通能力", "text": "我能清晰地表达自己的想法", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "沟通能力", "text": "我善于倾听他人的意见和建议", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "团队协作", "text": "我能在团队中发挥积极作用", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "团队协作", "text": "我懂得在团队中分工协作", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "问题解决", "text": "面对问题我能冷静分析并找到解决方案", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "问题解决", "text": "我善于从失败中总结经验", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "创新思维", "text": "我经常提出新颖的想法和方案", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "创新思维", "text": "我敢于尝试不同的方法解决问题", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "领导力", "text": "我能在团队中主动承担责任", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "领导力", "text": "我能激励他人共同完成目标", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "时间管理", "text": "我能合理安排自己的学习和生活时间", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "时间管理", "text": "我通常能按时完成任务", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "抗压能力", "text": "我在压力下仍能保持良好表现", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "抗压能力", "text": "我能积极面对困难和挑战", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
    ],
    "values": [
        {"dimension": "成就感", "text": "在工作中获得成就感对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "安全感", "text": "稳定的工作和收入对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "创造力", "text": "工作中发挥创意和想象力对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "人际关系", "text": "良好的同事关系对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "经济报酬", "text": "高收入和经济回报对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "社会贡献", "text": "对社会做出贡献对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "工作环境", "text": "舒适的工作环境和氛围对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
        {"dimension": "个人成长", "text": "持续学习和成长的机会对我很重要", "options": [{"label": "非常不同意", "value": 1}, {"label": "不同意", "value": 2}, {"label": "一般", "value": 3}, {"label": "同意", "value": 4}, {"label": "非常同意", "value": 5}]},
    ],
    "learning_habit": [
        {"dimension": "学习计划", "text": "我会制定详细的学习计划", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "学习计划", "text": "我能坚持执行学习计划", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "专注力", "text": "学习时我能保持长时间专注", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "专注力", "text": "我能在嘈杂环境中集中注意力", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "复习习惯", "text": "我会定期复习学过的知识", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "复习习惯", "text": "我善于利用零碎时间复习", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "知识整理", "text": "我会整理笔记和知识框架", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "知识整理", "text": "我喜欢用思维导图等方式组织知识", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "主动学习", "text": "我会主动查找额外的学习资料", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "主动学习", "text": "我会主动向老师或同学请教问题", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "时间分配", "text": "我能平衡不同科目的学习时间", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "时间分配", "text": "我很少拖延学习任务", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "自我评估", "text": "我会反思自己的学习效果", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
        {"dimension": "自我评估", "text": "我能准确判断自己的知识薄弱点", "options": [{"label": "从不", "value": 1}, {"label": "偶尔", "value": 2}, {"label": "有时", "value": 3}, {"label": "经常", "value": 4}, {"label": "总是", "value": 5}]},
    ],
    "readiness": [
        {"dimension": "自我认知", "text": "我清楚自己的兴趣和优势", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "自我认知", "text": "我有明确的职业价值观", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "职业了解", "text": "我了解目标职业的工作内容", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "职业了解", "text": "我了解目标行业的发展趋势", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "技能准备", "text": "我具备目标岗位所需的核心技能", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "技能准备", "text": "我持续在学习提升相关技能", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "心理准备", "text": "我对从学校到职场的转变有心理准备", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "心理准备", "text": "我有信心应对职场挑战", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "信息获取", "text": "我善于获取职业相关的信息", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "信息获取", "text": "我经常关注招聘信息和行业动态", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "决策能力", "text": "我能理性分析不同选择的利弊", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "决策能力", "text": "我能做出对自己有利的决策", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "行动规划", "text": "我有明确的求职或升学计划", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
        {"dimension": "行动规划", "text": "我正在按计划执行准备", "options": [{"label": "非常不符合", "value": 1}, {"label": "不符合", "value": 2}, {"label": "一般", "value": 3}, {"label": "符合", "value": 4}, {"label": "非常符合", "value": 5}]},
    ],
}

def get_dimensions_for_type(assessment_type: str) -> dict | list:
    mapping = {
        "holland": HOLLAND_DIMENSIONS,
        "ability": ABILITY_DIMENSIONS,
        "values": VALUES_DIMENSIONS,
        "learning_habit": LEARNING_HABIT_DIMENSIONS,
        "readiness": READINESS_DIMENSIONS,
    }
    return mapping.get(assessment_type, {})

def calculate_result(assessment_type: str, responses: list[dict], questions: list[dict]) -> dict:
    questions_data = DEFAULT_QUESTIONS.get(assessment_type, [])
    dim_scores = {}
    for i, resp in enumerate(responses):
        if i >= len(questions_data):
            break
        dim = questions_data[i]["dimension"]
        val = resp.get("answer_value", 3)
        if isinstance(val, dict):
            val = val.get("value", 3)
        if dim not in dim_scores:
            dim_scores[dim] = []
        dim_scores[dim].append(int(val) if not isinstance(val, int) else val)

    result = {}
    for dim, scores in dim_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        result[dim] = round(avg * 20, 1)

    if assessment_type == "holland":
        sorted_dims = sorted(result.items(), key=lambda x: x[1], reverse=True)
        top3 = [d[0] for d in sorted_dims[:3]]
        result["holland_code"] = "".join(top3)
        result["holland_description"] = get_holland_description(top3)

    return result

def get_holland_description(code: list[str]) -> str:
    descriptions = {
        "R": "现实型——喜欢动手操作、户外活动，适合工程技术类职业",
        "I": "研究型——喜欢思考分析、独立研究，适合科研学术类职业",
        "A": "艺术型——喜欢创意表达、自我展示，适合文化艺术类职业",
        "S": "社会型——喜欢助人合作、服务他人，适合教育医疗类职业",
        "E": "企业型——喜欢领导管理、商业开拓，适合管理创业类职业",
        "C": "常规型——喜欢有条理、按规则办事，适合行政管理类职业",
    }
    return "、".join([descriptions.get(c, "") for c in code])

class AssessmentService:
    async def get_assessments_status(self, user_id: str, db: AsyncSession) -> dict:
        result = await db.execute(
            select(Assessment).where(Assessment.user_id == user_id)
        )
        assessments = result.scalars().all()
        status_map = {a.type: a for a in assessments}
        result_dict = {}
        for at in ASSESSMENT_TYPES:
            if at in status_map:
                a = status_map[at]
                result_dict[at] = {
                    "id": str(a.id),
                    "type": a.type,
                    "status": a.status,
                    "current_question": a.current_question,
                    "total_questions": a.total_questions,
                    "started_at": a.started_at.isoformat() if a.started_at else None,
                    "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                    "created_at": a.created_at.isoformat(),
                }
            else:
                result_dict[at] = None
        return result_dict

    async def start_assessment(self, user_id: str, assessment_type: str, db: AsyncSession) -> tuple:
        existing = await db.execute(
            select(Assessment).where(
                and_(Assessment.user_id == user_id, Assessment.type == assessment_type)
            )
        )
        assessment = existing.scalar_one_or_none()

        questions_data = DEFAULT_QUESTIONS.get(assessment_type, [])
        question_records = []
        for i, q in enumerate(questions_data):
            question_records.append({
                "id": str(uuid4()),
                "type": assessment_type,
                "dimension": q["dimension"],
                "question_text": q["text"],
                "options": q["options"],
                "sort_order": i,
            })

        if assessment is None:
            assessment = Assessment(
                id=str(uuid4()),
                user_id=user_id,
                type=assessment_type,
                status="in_progress",
                current_question=0,
                total_questions=len(questions_data),
                started_at=datetime.now(),
            )
            db.add(assessment)
        else:
            # Clean up old responses and result when re-starting
            old_responses = await db.execute(
                select(AssessmentResponse).where(AssessmentResponse.assessment_id == assessment.id)
            )
            for resp in old_responses.scalars().all():
                await db.delete(resp)

            old_result = await db.execute(
                select(AssessmentResult).where(AssessmentResult.assessment_id == assessment.id)
            )
            old_ar = old_result.scalar_one_or_none()
            if old_ar is not None:
                await db.delete(old_ar)

            assessment.status = "in_progress"
            assessment.current_question = 0
            assessment.total_questions = len(questions_data)
            assessment.started_at = datetime.now()
            assessment.completed_at = None

        await db.flush()
        return assessment, question_records

    async def get_questions(self, assessment_type: str) -> list[dict]:
        questions_data = DEFAULT_QUESTIONS.get(assessment_type, [])
        return [
            {
                "id": str(uuid4()),
                "type": assessment_type,
                "dimension": q["dimension"],
                "question_text": q["text"],
                "options": q["options"],
                "sort_order": i,
            }
            for i, q in enumerate(questions_data)
        ]

    async def submit_answer(self, assessment_id: str, question_id: str, answer_value: dict, db: AsyncSession) -> dict:
        assessment = await db.get(Assessment, assessment_id)
        if assessment is None:
            raise ValueError("测评不存在")

        response = AssessmentResponse(
            assessment_id=assessment_id,
            question_id=question_id,
            answer_value=answer_value,
        )
        db.add(response)

        next_q = assessment.current_question + 1
        assessment.current_question = min(next_q, assessment.total_questions)

        await db.flush()
        return {
            "question_id": str(question_id),
            "current_question": assessment.current_question,
            "total_questions": assessment.total_questions,
            "is_last": assessment.current_question >= assessment.total_questions,
        }

    async def submit_assessment(self, assessment_id: str, db: AsyncSession) -> dict:
        assessment = await db.get(Assessment, assessment_id)
        if assessment is None:
            raise ValueError("测评不存在")

        stmt = select(AssessmentResponse).where(
            AssessmentResponse.assessment_id == assessment_id
        ).order_by(AssessmentResponse.created_at)
        result = await db.execute(stmt)
        responses = result.scalars().all()

        questions_data = DEFAULT_QUESTIONS.get(assessment.type, [])
        questions_with_ids = [
            {
                "id": str(uuid4()),
                "dimension": q["dimension"],
                "question_text": q["text"],
                "options": q["options"],
            }
            for q in questions_data
        ]

        response_dicts = [
            {"question_id": str(r.question_id), "answer_value": r.answer_value}
            for r in responses
        ]

        result_data = calculate_result(assessment.type, response_dicts, questions_with_ids)

        ai_summary = ""
        try:
            ai_result = await ai_service.analyze_assessment_result(
                assessment.type, response_dicts, questions_with_ids
            )
            ai_summary = ai_result.get("ai_analysis", "")
        except Exception:
            pass

        # Check if result already exists (update instead of create)
        existing_result_stmt = select(AssessmentResult).where(AssessmentResult.assessment_id == assessment_id)
        existing_result = await db.execute(existing_result_stmt)
        assessment_result = existing_result.scalar_one_or_none()

        summary_text = ai_summary or generate_default_summary(assessment.type, result_data)

        if assessment_result is not None:
            assessment_result.result_data = result_data
            assessment_result.summary = summary_text
        else:
            assessment_result = AssessmentResult(
                assessment_id=assessment_id,
                type=assessment.type,
                result_data=result_data,
                summary=summary_text,
            )
            db.add(assessment_result)

        assessment.status = "completed"
        assessment.completed_at = datetime.now()

        history = AssessmentHistory(
            user_id=assessment.user_id,
            type=assessment.type,
            result_snapshot=result_data,
            version=await self._get_next_version(assessment.user_id, assessment.type, db),
        )
        db.add(history)

        await db.flush()
        return {
            "assessment_id": str(assessment_id),
            "result": {
                "id": str(assessment_result.id),
                "type": assessment_result.type,
                "result_data": result_data,
                "summary": assessment_result.summary,
                "created_at": assessment_result.created_at.isoformat(),
            },
        }

    async def get_result(self, assessment_id: str, db: AsyncSession) -> dict | None:
        result = await db.execute(
            select(AssessmentResult).where(AssessmentResult.assessment_id == assessment_id)
        )
        ar = result.scalar_one_or_none()
        if ar is None:
            return None
        return {
            "id": str(ar.id),
            "type": ar.type,
            "result_data": ar.result_data,
            "summary": ar.summary,
            "created_at": ar.created_at.isoformat(),
        }

    async def get_history(self, user_id: str, db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(AssessmentHistory)
            .where(AssessmentHistory.user_id == user_id)
            .order_by(AssessmentHistory.created_at.desc())
        )
        records = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "type": r.type,
                "result_snapshot": r.result_snapshot,
                "version": r.version,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]

    async def get_type_history(self, user_id: str, assessment_type: str, db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(AssessmentHistory)
            .where(
                and_(
                    AssessmentHistory.user_id == user_id,
                    AssessmentHistory.type == assessment_type,
                )
            )
            .order_by(AssessmentHistory.created_at.desc())
        )
        records = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "type": r.type,
                "result_snapshot": r.result_snapshot,
                "version": r.version,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]

    async def _get_next_version(self, user_id: str, assessment_type: str, db: AsyncSession) -> int:
        result = await db.execute(
            select(AssessmentHistory)
            .where(
                and_(
                    AssessmentHistory.user_id == user_id,
                    AssessmentHistory.type == assessment_type,
                )
            )
            .order_by(AssessmentHistory.version.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        return (last.version + 1) if last else 1

    async def get_growth_profile(self, user_id: str, db: AsyncSession) -> dict:
        # Get all completed assessments with their results
        stmt = (
            select(Assessment)
            .where(and_(Assessment.user_id == user_id, Assessment.status == "completed"))
        )
        result = await db.execute(stmt)
        assessments = result.scalars().all()

        profile = {}
        completed_count = 0
        total_count = len(ASSESSMENT_TYPES)

        for a in assessments:
            r_stmt = select(AssessmentResult).where(AssessmentResult.assessment_id == a.id)
            r_result = await db.execute(r_stmt)
            ar = r_result.scalar_one_or_none()
            if ar is None:
                continue
            completed_count += 1
            profile[a.type] = {
                "id": str(ar.id),
                "type": ar.type,
                "result_data": ar.result_data,
                "summary": ar.summary,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }

        # Calculate overall scores per assessment type (average of dimension scores)
        overall = {}
        for atype, data in profile.items():
            rd = data["result_data"]
            numeric_vals = [v for k, v in rd.items() if isinstance(v, (int, float))]
            overall[atype] = round(sum(numeric_vals) / len(numeric_vals), 1) if numeric_vals else 0

        # Generate growth suggestions based on all assessment results
        suggestions = generate_growth_suggestions(profile, overall)

        return {
            "completed_count": completed_count,
            "total_count": total_count,
            "assessments": profile,
            "overall_scores": overall,
            "overall_avg": round(sum(overall.values()) / len(overall), 1) if overall else 0,
            "suggestions": suggestions,
        }

assessment_service = AssessmentService()


def generate_growth_suggestions(profile: dict, overall_scores: dict) -> dict:
    """基于五项测评结果生成综合成长建议"""
    assessments = profile
    suggestions = {
        "strengths": [],       # 优势亮点
        "improvements": [],    # 待提升领域
        "career": [],          # 职业发展建议
        "action_plan": [],     # 具体行动计划
        "cross_analysis": [],  # 交叉分析洞察
    }

    # ========== 1. 霍兰德兴趣分析 ==========
    holland = assessments.get("holland")
    if holland:
        rd = holland["result_data"]
        code = rd.get("holland_code", "")
        # 提取各维度分数
        holland_dims = {k: v for k, v in rd.items() if isinstance(v, (int, float))}
        sorted_dims = sorted(holland_dims.items(), key=lambda x: x[1], reverse=True)
        top_dim = sorted_dims[0] if sorted_dims else None
        bottom_dim = sorted_dims[-1] if sorted_dims else None

        if top_dim:
            dim_labels = {"R": "现实型", "I": "研究型", "A": "艺术型", "S": "社会型", "E": "企业型", "C": "常规型"}
            suggestions["strengths"].append({
                "source": "holland",
                "icon": "🎯",
                "text": f"你的兴趣倾向以{dim_labels.get(top_dim[0], top_dim[0])}（{top_dim[0]}）为主，得分 {round(top_dim[1])} 分，这是你最核心的驱动力。"
            })

        if code:
            career_map = {
                "R": "工程技术、机械制造、IT运维、建筑设计等实操型岗位",
                "I": "科研分析、数据研究、学术研究、技术开发等研究型岗位",
                "A": "创意设计、内容创作、文化艺术、产品设计等创意型岗位",
                "S": "教育培训、心理咨询、社会工作、医疗护理等服务型岗位",
                "E": "市场营销、项目管理、创业、商务拓展等管理型岗位",
                "C": "财务审计、行政管理、数据分析、质量管理等规范型岗位",
            }
            top_code = code[0] if code else ""
            if top_code in career_map:
                suggestions["career"].append({
                    "source": "holland",
                    "icon": "💼",
                    "text": f"基于霍兰德代码 {code}，推荐关注：{career_map.get(top_code, '')}"
                })

        if bottom_dim and top_dim and top_dim[1] - bottom_dim[1] > 30:
            dim_labels = {"R": "现实型", "I": "研究型", "A": "艺术型", "S": "社会型", "E": "企业型", "C": "常规型"}
            suggestions["cross_analysis"].append({
                "source": "holland",
                "icon": "📊",
                "text": f"兴趣分化明显：{dim_labels.get(top_dim[0], top_dim[0])}远高于{dim_labels.get(bottom_dim[0], bottom_dim[0])}，建议聚焦优势方向，同时适当拓展弱势领域。"
            })

    # ========== 2. 能力自评分析 ==========
    ability = assessments.get("ability")
    if ability:
        rd = ability["result_data"]
        ability_dims = {k: v for k, v in rd.items() if isinstance(v, (int, float))}
        sorted_a = sorted(ability_dims.items(), key=lambda x: x[1], reverse=True)
        strong = [d for d in sorted_a if d[1] >= 70]
        weak = [d for d in sorted_a if d[1] < 60]

        if strong:
            names = "、".join([d[0] for d in strong[:3]])
            suggestions["strengths"].append({
                "source": "ability",
                "icon": "💪",
                "text": f"你的核心能力优势：{names}，这些是你在职场中的竞争力所在。"
            })

        if weak:
            for dim_name, score in weak[:2]:
                improvement_map = {
                    "学习能力": "尝试费曼学习法：学完一个知识点后用自己的话讲给别人听，加深理解。",
                    "沟通能力": "每周主动参与一次小组讨论或课堂发言，刻意练习表达和倾听。",
                    "团队协作": "参加一个社团或项目团队，在实践中学习分工配合和冲突处理。",
                    "问题解决": "遇到问题时先写下问题定义，列出3个可能方案再行动，培养结构化思维。",
                    "创新思维": "每周花30分钟做头脑风暴，尝试用不同方法解决同一个问题。",
                    "领导力": "主动承担一次小组作业的组长角色，练习目标分解和任务分配。",
                    "时间管理": "使用番茄工作法（25分钟专注+5分钟休息），记录每天时间去向。",
                    "抗压能力": "建立运动习惯（每周3次），学习正念呼吸法，逐步提升心理韧性。",
                }
                suggestions["improvements"].append({
                    "source": "ability",
                    "icon": "📈",
                    "dimension": dim_name,
                    "score": round(score),
                    "text": f"「{dim_name}」得分 {round(score)} 分，建议：{improvement_map.get(dim_name, '制定针对性提升计划并持续练习。')}"
                })

    # ========== 3. 价值观分析 ==========
    values = assessments.get("values")
    if values:
        rd = values["result_data"]
        values_dims = {k: v for k, v in rd.items() if isinstance(v, (int, float))}
        sorted_v = sorted(values_dims.items(), key=lambda x: x[1], reverse=True)
        top_values = sorted_v[:3]
        bottom_values = sorted_v[-2:] if len(sorted_v) >= 2 else []

        if top_values:
            names = "、".join([d[0] for d in top_values])
            suggestions["strengths"].append({
                "source": "values",
                "icon": "⭐",
                "text": f"你最看重的职业价值：{names}。选择工作时优先考虑这些维度，会让你更有满足感。"
            })

        if top_values and holland:
            top_value_name = top_values[0][0]
            holland_rd = holland["result_data"]
            holland_code = holland_rd.get("holland_code", "")
            # 检查价值观与兴趣的匹配度
            value_holland_map = {
                "成就感": ["E", "I", "A"],
                "创造力": ["A", "I", "E"],
                "人际关系": ["S", "E"],
                "社会贡献": ["S"],
                "经济报酬": ["E", "R"],
                "安全感": ["C", "R"],
                "个人成长": ["I", "A", "E"],
                "工作环境": ["S", "A", "C"],
            }
            compatible_codes = value_holland_map.get(top_value_name, [])
            if holland_code and compatible_codes:
                match_count = sum(1 for c in holland_code if c in compatible_codes)
                if match_count >= 2:
                    suggestions["cross_analysis"].append({
                        "source": "values",
                        "icon": "✅",
                        "text": f"你的核心价值观「{top_value_name}」与兴趣代码 {holland_code} 高度契合，说明你的职业方向与内在驱动力一致。"
                    })
                elif match_count == 0:
                    suggestions["cross_analysis"].append({
                        "source": "values",
                        "icon": "⚠️",
                        "text": f"你最看重的「{top_value_name}」与兴趣代码 {holland_code} 存在一定张力。建议探索能同时满足兴趣和价值观的交叉领域。"
                    })

    # ========== 4. 学习习惯分析 ==========
    learning = assessments.get("learning_habit")
    if learning:
        rd = learning["result_data"]
        learning_dims = {k: v for k, v in rd.items() if isinstance(v, (int, float))}
        sorted_l = sorted(learning_dims.items(), key=lambda x: x[1], reverse=True)
        weak_l = [d for d in sorted_l if d[1] < 60]
        strong_l = [d for d in sorted_l if d[1] >= 70]

        if strong_l:
            names = "、".join([d[0] for d in strong_l[:2]])
            suggestions["strengths"].append({
                "source": "learning_habit",
                "icon": "📚",
                "text": f"你的学习习惯优势：{names}，这些好习惯会持续为你的学业和职业赋能。"
            })

        if weak_l:
            for dim_name, score in weak_l[:2]:
                habit_map = {
                    "学习计划": "建议使用 Notion 或纸质手账，每周一制定本周学习目标，每天回顾完成度。",
                    "专注力": "尝试番茄工作法，学习时手机开启勿扰模式，逐步延长专注时间。",
                    "复习习惯": "采用间隔重复法（Anki），按1天-3天-7天-14天的节奏复习。",
                    "知识整理": "每学完一章用思维导图整理框架，周末做一次知识串联。",
                    "主动学习": "每周至少向老师或同学提一个有深度的问题，培养好奇心。",
                    "时间分配": "用时间日志记录3天的时间去向，找出可优化的时间段。",
                    "学习环境": "固定一个学习场所，保持桌面整洁，减少干扰因素。",
                    "自我评估": "每月做一次自我复盘，对照目标检查进度和差距。",
                }
                suggestions["improvements"].append({
                    "source": "learning_habit",
                    "icon": "📝",
                    "dimension": dim_name,
                    "score": round(score),
                    "text": f"「{dim_name}」得分 {round(score)} 分，建议：{habit_map.get(dim_name, '制定改进计划并坚持执行。')}"
                })

    # ========== 5. 准备度分析 ==========
    readiness = assessments.get("readiness")
    if readiness:
        rd = readiness["result_data"]
        readiness_dims = {k: v for k, v in rd.items() if isinstance(v, (int, float))}
        sorted_r = sorted(readiness_dims.items(), key=lambda x: x[1], reverse=True)
        weak_r = [d for d in sorted_r if d[1] < 60]
        strong_r = [d for d in sorted_r if d[1] >= 70]

        if strong_r:
            names = "、".join([d[0] for d in strong_r[:2]])
            suggestions["strengths"].append({
                "source": "readiness",
                "icon": "🚀",
                "text": f"你的职场准备优势：{names}，说明你在这些方面已有良好基础。"
            })

        if weak_r:
            for dim_name, score in weak_r[:2]:
                ready_map = {
                    "自我认知": "完成一次MBTI或优势识别测试，找3位了解你的朋友做360度反馈。",
                    "职业了解": "每周访谈一位目标行业的从业者，了解真实工作内容和要求。",
                    "技能准备": "对照目标岗位的JD，列出技能差距清单，制定3个月学习计划。",
                    "心理准备": "参加模拟面试或职场体验活动，提前感受职场氛围。",
                    "信息获取": "关注3-5个行业公众号/播客，加入校友职业交流群。",
                    "决策能力": "学习SWOT分析法，对每个选项列出优劣势，做理性决策。",
                    "行动规划": "制定SMART目标：具体的、可衡量的、可达到的、相关的、有时限的。",
                    "资源利用": "主动联系学校就业中心，参加校园招聘会和校友导师计划。",
                }
                suggestions["improvements"].append({
                    "source": "readiness",
                    "icon": "🎯",
                    "dimension": dim_name,
                    "score": round(score),
                    "text": f"「{dim_name}」得分 {round(score)} 分，建议：{ready_map.get(dim_name, '制定行动计划并立即开始执行。')}"
                })

    # ========== 6. 综合行动计划 ==========
    # 找出所有测评中最需要提升的维度
    all_weak = []
    for s in suggestions["improvements"]:
        all_weak.append(s)

    if all_weak:
        all_weak.sort(key=lambda x: x.get("score", 100))
        top_weak = all_weak[0]
        suggestions["action_plan"].append({
            "icon": "🏆",
            "priority": "高",
            "text": f"最优先提升项：「{top_weak.get('dimension', '')}」（{top_weak.get('score', 0)}分）。{top_weak['text'].split('建议：')[-1] if '建议：' in top_weak.get('text', '') else ''}"
        })

    if len(all_weak) >= 2:
        second = all_weak[1]
        suggestions["action_plan"].append({
            "icon": "📋",
            "priority": "中",
            "text": f"次优先提升项：「{second.get('dimension', '')}」（{second.get('score', 0)}分）。{second['text'].split('建议：')[-1] if '建议：' in second.get('text', '') else ''}"
        })

    # 基于综合得分给出总体建议
    avg = sum(overall_scores.values()) / len(overall_scores) if overall_scores else 0
    if avg >= 75:
        suggestions["action_plan"].append({
            "icon": "🌟",
            "priority": "建议",
            "text": "你的综合素质优秀，建议将精力聚焦在职业方向的精准定位和核心技能的深度打磨上。"
        })
    elif avg >= 60:
        suggestions["action_plan"].append({
            "icon": "📊",
            "priority": "建议",
            "text": "你的综合素质良好，建议制定3个月提升计划，重点突破1-2个薄弱环节，同时发挥优势。"
        })
    else:
        suggestions["action_plan"].append({
            "icon": "💡",
            "priority": "建议",
            "text": "建议从最基础的自我认知和学习习惯入手，先建立清晰的自我定位，再逐步提升其他方面。"
        })

    # 跨测评交叉洞察
    if ability and learning:
        ability_avg = overall_scores.get("ability", 0)
        learning_avg = overall_scores.get("learning_habit", 0)
        if ability_avg >= 70 and learning_avg < 60:
            suggestions["cross_analysis"].append({
                "source": "cross",
                "icon": "💡",
                "text": "你的能力不错但学习习惯偏弱，说明还有很大潜力未释放。改善学习习惯后，能力提升速度会显著加快。"
            })
        elif learning_avg >= 70 and ability_avg < 60:
            suggestions["cross_analysis"].append({
                "source": "cross",
                "icon": "💡",
                "text": "你的学习习惯良好但自评能力偏低，可能是自信心不足。建议通过实际项目成果来验证和建立能力自信。"
            })

    if readiness and holland:
        readiness_avg = overall_scores.get("readiness", 0)
        if readiness_avg >= 70:
            suggestions["cross_analysis"].append({
                "source": "cross",
                "icon": "✅",
                "text": "你的职业准备度较高，结合明确的兴趣方向，你已经具备了较好的求职或深造基础。建议立即行动。"
            })
        elif readiness_avg < 50:
            suggestions["cross_analysis"].append({
                "source": "cross",
                "icon": "⏰",
                "text": "你的职业准备度还有提升空间，建议尽早开始职业规划，将兴趣转化为具体的职业目标和行动计划。"
            })

    return suggestions


def generate_default_summary(assessment_type: str, result_data: dict) -> str:
    summaries = {
        "holland": f"你的霍兰德代码为 {result_data.get('holland_code', '未知')}，{result_data.get('holland_description', '')}",
        "ability": "能力自评完成，各维度得分反映了你对自己能力的认知。建议结合客观表现进行综合评估。",
        "values": "价值观测评完成，了解自己的职业价值观有助于做出更符合内心的职业选择。",
        "learning_habit": "学习习惯测评完成，良好的学习习惯是学业成功的基础。建议针对薄弱维度制定改进计划。",
        "readiness": "准备度测评完成，了解自己的准备状态可以帮助你更有针对性地进行求职或深造准备。",
    }
    return summaries.get(assessment_type, "测评完成")
