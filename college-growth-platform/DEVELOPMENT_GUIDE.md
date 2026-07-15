# 大学生成长赋能平台 —— 零基础全栈开发指南

> 本文档面向零基础开发者，提供从零搭建完整前后端项目的详细步骤。  
> 每个阶段附有 **AI 提示词（Prompt）**，可直接复制给 Qoder / Trae / Claude Code 等 AI 编程工具使用。

---

## 一、项目概述

### 1.1 项目简介

大学生成长赋能平台是一个帮助大学生进行自我评估和成长规划的 Web 应用。系统提供 5 种专业测评（霍兰德兴趣、能力自评、职业价值观、学习习惯、准备度），完成全部测评后生成综合成长画像。

### 1.2 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端框架 | FastAPI | 0.109.0 | Python 异步 Web 框架 |
| ORM | SQLAlchemy | 2.0.25 | 异步数据库操作 |
| 数据库 | SQLite | - | 轻量级嵌入式数据库 |
| 数据库驱动 | aiosqlite | 0.19.0 | SQLAlchemy 异步 SQLite 驱动 |
| 前端框架 | Next.js | 16.x | React 全栈框架（App Router） |
| UI 样式 | Tailwind CSS | 3.4.x | 原子化 CSS 框架 |
| 状态管理 | Zustand | 4.5.x | 轻量级 React 状态管理 |
| HTTP 客户端 | Axios | 1.6.x | 前端 HTTP 请求库 |
| 语言 | TypeScript | 5.x | 前端类型安全 |

### 1.3 项目目录结构

```
college-growth-platform/
├── backend/                    # 后端
│   ├── app/
│   │   ├── api/v1/assessment/  # 测评 API 路由
│   │   ├── models/             # 数据库模型（ORM）
│   │   ├── schemas/            # 请求/响应数据校验
│   │   ├── services/           # 业务逻辑层
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── dependencies.py     # 依赖注入（认证等）
│   │   └── main.py             # 应用入口
│   ├── requirements.txt        # Python 依赖
│   └── .env                    # 环境变量
└── frontend/                   # 前端
    ├── src/
    │   ├── app/assessment/     # 测评页面（Next.js App Router）
    │   │   ├── page.tsx        # 测评中心首页
    │   │   ├── layout.tsx      # 测评模块布局
    │   │   ├── [type]/page.tsx # 答题页面（动态路由）
    │   │   ├── result/[id]/    # 结果页面
    │   │   └── profile/        # 成长画像页面
    │   ├── components/         # 可复用组件
    │   ├── hooks/              # 自定义 Hooks
    │   ├── lib/                # 工具函数（API 封装）
    │   ├── store/              # Zustand 状态管理
    │   └── types/              # TypeScript 类型定义
    ├── package.json
    ├── tailwind.config.ts
    └── tsconfig.json
```

---

## 二、环境准备

### 2.1 安装必要软件

| 软件 | 最低版本 | 下载地址 | 验证命令 |
|------|---------|---------|---------|
| Python | 3.10+ | https://www.python.org/downloads/ | `python --version` |
| Node.js | 18+ (推荐 20 LTS) | https://nodejs.org/ | `node --version` |
| Git | 任意 | https://git-scm.com/ | `git --version` |

> **注意**：本项目使用 SQLite，无需安装数据库。

### 2.2 AI 提示词 —— 环境检查

```
请帮我检查当前开发环境：
1. 检查 Python 版本是否 >= 3.10
2. 检查 Node.js 版本是否 >= 18
3. 检查 npm 是否可用
4. 如果缺少任何软件，告诉我安装步骤
```

---

## 三、后端开发

### 阶段 1：项目初始化

#### AI 提示词

```
帮我创建一个 FastAPI 后端项目，要求如下：

项目名称：college-growth-platform/backend

技术栈：
- FastAPI 0.109.0
- SQLAlchemy 2.0.25（异步模式）
- SQLite 数据库（使用 aiosqlite 驱动）
- pydantic-settings 管理配置

请创建以下文件结构：
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 应用入口，配置 CORS，注册路由
│   ├── config.py          # 使用 pydantic-settings 读取 .env
│   ├── database.py        # 异步引擎和会话管理
│   ├── dependencies.py    # 用户认证依赖注入
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py        # 用户模型
│   │   └── assessment.py  # 测评相关模型（5张表）
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── assessment.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py      # AI 分析服务
│   │   └── assessment_service.py  # 测评业务逻辑
│   └── api/v1/assessment/
│       ├── __init__.py     # API 路由定义
├── requirements.txt
└── .env

关键要求：
1. 数据库使用 SQLite+aiosqlite，连接字符串为 sqlite+aiosqlite:///./college_growth.db
2. SQLite 需要设置 connect_args={"check_same_thread": False}
3. 所有主键使用 String(36) 类型，默认值为 str(uuid4())，不要用 PostgreSQL 的 UUID 类型
4. 所有枚举字段使用 String(20) 代替 Enum 类型
5. CORS 允许 http://localhost:3000
6. 开发模式下无需真实认证，自动创建一个默认用户
```

### 阶段 2：数据库模型

#### 数据表设计

系统包含 5 张核心数据表：

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `users` | 用户表 | id, email, nickname, role |
| `assessments` | 测评记录 | id, user_id, type, status, current_question |
| `assessment_questions` | 题库 | id, type, dimension, question_text, options(JSON) |
| `assessment_responses` | 用户回答 | id, assessment_id, question_id, answer_value(JSON) |
| `assessment_results` | 测评结果 | id, assessment_id(unique), type, result_data(JSON), summary |
| `assessment_histories` | 历史记录 | id, user_id, type, result_snapshot(JSON), version |

#### AI 提示词

```
请创建 SQLAlchemy 2.0 异步模型，要求如下：

1. User 模型 (users 表)：
   - id: String(36) 主键，default=lambda: str(uuid4())
   - email: String(255) 唯一索引
   - nickname: String(50)
   - password_hash: String(255)
   - role: String(20) 默认 "student"
   - is_active: Boolean 默认 True
   - created_at, updated_at: DateTime

2. Assessment 模型 (assessments 表)：
   - id: String(36) 主键
   - user_id: String(36) 外键关联 users
   - type: String(20) 测评类型 (holland/ability/values/learning_habit/readiness)
   - status: String(20) 默认 "not_started" (not_started/in_progress/completed)
   - current_question: Integer 当前题目索引
   - total_questions: Integer 总题数
   - started_at, completed_at, created_at, updated_at: DateTime
   - 关系：responses (cascade delete), result (uselist=False, cascade delete)

3. AssessmentResponse 模型 (assessment_responses 表)：
   - id: String(36) 主键
   - assessment_id: String(36) 外键
   - question_id: String(36)
   - answer_value: JSON 存储 {"value": 1-5}
   - created_at: DateTime

4. AssessmentResult 模型 (assessment_results 表)：
   - id: String(36) 主键
   - assessment_id: String(36) 外键，unique=True（一个测评只能有一个结果）
   - type: String(20)
   - result_data: JSON 存储各维度分数
   - summary: Text AI 生成的总结
   - created_at: DateTime

5. AssessmentHistory 模型 (assessment_histories 表)：
   - id: String(36) 主键
   - user_id, type, result_snapshot(JSON), version(Integer)

重要注意事项：
- 不要使用 from sqlalchemy.dialects.postgresql import UUID
- 所有主键用 String(36) + default=lambda: str(uuid4())
- 不要用 Enum 类型，用 String(20) 代替
```

### 阶段 3：测评题库与业务逻辑

#### 5 种测评的维度设计

| 测评类型 | 维度 | 题目数 |
|---------|------|--------|
| 霍兰德兴趣 (holland) | R现实/I研究/A艺术/S社会/E企业/C常规 | 18题 (每维度3题) |
| 能力自评 (ability) | 学习/沟通/协作/问题解决/创新/领导力/时间管理/抗压 | 16题 (每维度2题) |
| 职业价值观 (values) | 成就感/安全感/创造力/人际关系/经济报酬/社会贡献/工作环境/个人成长 | 8题 |
| 学习习惯 (learning_habit) | 学习计划/专注力/复习习惯/知识整理/主动学习/时间分配/自我评估 | 14题 (每维度2题) |
| 准备度 (readiness) | 自我认知/职业了解/技能准备/心理准备/信息获取/决策能力/行动规划 | 14题 (每维度2题) |

#### AI 提示词

```
请创建 assessment_service.py，包含完整的测评业务逻辑：

1. 题库定义 (DEFAULT_QUESTIONS 字典)：
   - 5 种测评类型，每种包含若干题目
   - 每题结构：{"dimension": "维度名", "text": "题目文本", "options": [{"label": "非常不同意", "value": 1}, ...{"label": "非常同意", "value": 5}]}
   - 霍兰德：18题，6维度(R/I/A/S/E/C)各3题
   - 能力自评：16题，8维度各2题
   - 价值观：8题，8维度各1题
   - 学习习惯：14题，7维度各2题
   - 准备度：14题，7维度各2题

2. 核心方法：
   a. get_assessments_status(user_id, db) -> dict
      返回 {holland: Assessment|None, ability: ..., ...} 格式的状态映射

   b. start_assessment(user_id, type, db) -> (Assessment, questions)
      - 如果已有同类型测评，清理旧的回答和结果（因为 assessment_result 的 assessment_id 有 unique 约束）
      - 为每道题生成随机 UUID 作为 id
      - 返回测评记录和题目列表

   c. submit_answer(assessment_id, question_id, answer_value, db) -> dict
      存储回答，更新 current_question 进度

   d. submit_assessment(assessment_id, db) -> dict
      - 按 created_at 排序获取所有回答
      - 调用 calculate_result 计算分数
      - 如果已存在 AssessmentResult 则更新，否则新建（幂等处理）
      - 创建 AssessmentHistory 记录
      - 更新 assessment 状态为 completed

   e. get_growth_profile(user_id, db) -> dict
      聚合所有已完成测评的结果，计算各测评综合得分和总体平均分

3. 分数计算逻辑 (calculate_result 函数)：
   - 按题库顺序将回答与题目维度对应（不依赖 question_id 匹配）
   - 每个维度取回答均值，乘以 20 转换为 0-100 分
   - 霍兰德特殊处理：取 top3 维度生成霍兰德代码（如 "EIA"）
```

### 阶段 4：API 路由

#### AI 提示词

```
请创建 FastAPI API 路由，前缀为 /api/v1/assessments，包含以下端点：

1. GET "" - 获取所有测评状态
   返回：{holland: {id, type, status, ...}|null, ability: ...|null, ...}

2. POST "/{assessment_type}/start" - 开始测评
   返回：{assessment: {...}, questions: [{id, type, dimension, question_text, options, sort_order}]}

3. POST "/{assessment_id}/answer" - 提交单个答案
   请求体：{question_id: str, answer_value: {value: number}}
   返回：{question_id, current_question, total_questions, is_last}

4. POST "/{assessment_id}/submit" - 提交整个测评
   返回：{assessment_id, result: {id, type, result_data, summary, created_at}}

5. GET "/{assessment_id}/result" - 获取测评结果

6. GET "/growth-profile" - 获取成长画像（注意：此路由要定义在 /{assessment_type} 之前，避免路径冲突）

7. GET "/history" - 获取历史记录

注意事项：
- growth-profile 路由必须放在 /{assessment_type}/questions 之前
- 所有接口需要 get_current_user 依赖注入
- 错误处理：测评不存在返回 404
```

### 阶段 5：认证与配置

#### AI 提示词

```
请创建开发模式的认证系统：

1. dependencies.py：
   - 使用 HTTPBearer(auto_error=False) 使认证可选
   - 定义 DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
   - get_or_create_dev_user：自动创建/获取默认开发用户
   - get_current_user：
     - 如果没有 token → 返回开发用户
     - 如果 token 无效 → 返回开发用户（容错）
     - 如果 token 有效 → 解码获取用户

2. config.py：
   - 使用 pydantic-settings 的 BaseSettings
   - 从 .env 文件读取配置
   - 关键配置项：
     DATABASE_URL=sqlite+aiosqlite:///./college_growth.db
     JWT_SECRET_KEY=dev-secret-key
     AI_API_KEY=（留空则不调用 AI）
     CORS_ORIGINS=["http://localhost:3000"]

3. database.py：
   - 检测 SQLite 时自动添加 check_same_thread=False
   - 提供 get_db 异步生成器（自动 commit/rollback）
```

### 阶段 6：启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：访问 http://localhost:8000/docs 查看 Swagger 文档。

---

## 四、前端开发

### 阶段 1：项目初始化

#### AI 提示词

```
帮我用 Next.js 创建一个前端项目，要求如下：

1. 使用 npx create-next-app@latest frontend 初始化
   - 选择 TypeScript
   - 选择 App Router
   - 选择 Tailwind CSS
   - 选择 src/ 目录结构

2. 安装额外依赖：
   npm install zustand axios

3. 升级 Next.js 到最新版（避免 Node.js 兼容性问题）：
   npm install next@latest

4. 创建以下目录结构：
   src/
   ├── app/assessment/
   │   ├── page.tsx          # 测评中心
   │   ├── layout.tsx        # 布局
   │   ├── [type]/page.tsx   # 答题页
   │   ├── result/[id]/page.tsx  # 结果页
   │   └── profile/page.tsx  # 成长画像
   ├── components/assessment/
   │   ├── LikertScale.tsx   # 李克特量表组件
   │   ├── ProgressBar.tsx   # 进度条组件
   │   └── ResultRadar.tsx   # 雷达图组件
   ├── store/assessmentStore.ts  # Zustand 状态
   ├── lib/api.ts            # Axios 封装
   └── types/assessment.ts   # 类型定义

5. tailwind.config.ts 配置扫描路径：
   content: ['./src/pages/**/*.{js,ts,jsx,tsx,mdx}',
             './src/components/**/*.{js,ts,jsx,tsx,mdx}',
             './src/app/**/*.{js,ts,jsx,tsx,mdx}']

6. tsconfig.json 配置路径别名：
   "paths": {"@/*": ["./src/*"]}
```

### 阶段 2：类型定义与 API 封装

#### AI 提示词

```
请创建前端的类型定义和 API 封装层：

1. types/assessment.ts：
   - AssessmentType = 'holland' | 'ability' | 'values' | 'learning_habit' | 'readiness'
   - AssessmentStatus = 'not_started' | 'in_progress' | 'completed'
   - AssessmentQuestion 接口：id, type, dimension?, question_text, options[{label,value}], sort_order
   - Assessment 接口：id, type, status, current_question, total_questions, started_at?, completed_at?, created_at
   - AssessmentResult 接口：id, type, result_data: Record<string, number|string>, summary?, created_at
   - AssessmentStatusMap：5种类型各自对应 Assessment | null
   - 常量：ASSESSMENT_LABELS（中文标签）、ASSESSMENT_DESCRIPTIONS（描述）、ASSESSMENT_ICONS（emoji图标）

2. lib/api.ts：
   - 创建 axios 实例，baseURL 为 process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
   - 请求拦截器：从 localStorage 读取 token 添加到 Authorization header
   - 响应拦截器：直接返回 response.data（不要返回完整 response）
   - 错误处理：不要自动跳转登录页（开发模式无需认证）
   - 导出 apiService 对象，包含 get/post/put/delete 方法

3. store/assessmentStore.ts (Zustand)：
   - 状态：statusMap, currentAssessment, currentQuestions, currentIndex, answers, result, growthProfile, isLoading, error
   - 方法：
     fetchStatus() → GET /assessments
     startAssessment(type) → POST /assessments/{type}/start
     submitAnswer(id, questionId, value) → POST /assessments/{id}/answer，发送 {question_id, answer_value: {value}}
     submitAssessment(id) → POST /assessments/{id}/submit
     fetchResult(id) → GET /assessments/{id}/result
     fetchGrowthProfile() → GET /assessments/growth-profile
     nextQuestion(), prevQuestion(), setAnswer(), resetCurrent()
```

### 阶段 3：测评中心首页

#### AI 提示词

```
请创建测评中心首页 src/app/assessment/page.tsx：

功能要求：
1. 页面加载时调用 fetchStatus() 获取所有测评状态
2. 显示 5 张测评卡片（2列网格布局），每张包含：
   - emoji 图标 + 中文标题 + 描述
   - 状态徽章（未开始/进行中/已完成）
   - 已完成 → 显示"查看结果"链接
   - 未开始 → 显示"开始测评"按钮
   - 进行中 → 显示"继续答题"按钮
3. 点击按钮使用 router.push 导航到 /assessment/{slug}
   URL 映射：holland→holland, ability→ability, values→values, 
            learning_habit→learning-habit, readiness→readiness
4. 右上角显示"成长画像"按钮（至少完成1项测评后显示），导航到 /assessment/profile
   按钮文字：全部完成时显示"查看成长画像"，否则显示"成长画像 (N/5)"

样式要求：
- 使用 Tailwind CSS
- 卡片有 hover 阴影效果
- 响应式布局 sm:grid-cols-2
```

### 阶段 4：答题页面

#### AI 提示词

```
请创建答题页面 src/app/assessment/[type]/page.tsx：

功能要求：
1. 从 URL 参数获取测评类型 slug，映射为内部类型名
   TYPE_MAP: holland→holland, ability→ability, values→values, 
            learning-habit→learning_habit, readiness→readiness
2. 页面加载时自动调用 startAssessment(type) 开始测评
3. 显示当前题目：
   - 进度条（第N题/共M题）
   - 维度标签（如"现实型"）
   - 题目文本
   - 5 个选项的李克特量表（Likert Scale）
4. 选择答案后自动：
   - 调用 submitAnswer 提交到后端
   - 如果不是最后一题 → nextQuestion()
   - 如果是最后一题 → submitAssessment() → 导航到结果页
5. 支持"上一题"按钮回退
6. 提交过程中禁用选项防止重复点击

URL 路由说明：
- /assessment/holland → 霍兰德测评
- /assessment/ability → 能力自评
- /assessment/values → 价值观测评
- /assessment/learning-habit → 学习习惯（注意 URL 用连字符）
- /assessment/readiness → 准备度测评
```

### 阶段 5：结果页面

#### AI 提示词

```
请创建结果页面 src/app/assessment/result/[id]/page.tsx：

功能要求：
1. 从 URL 获取 assessmentId，调用 fetchResult(assessmentId) 获取结果
2. 显示内容：
   - 测评类型标题
   - 霍兰德代码（仅霍兰德测评有，result_data.holland_code 为字符串时显示）
   - 霍兰德描述（result_data.holland_description）
   - 雷达图（排除 holland_code 和 holland_description 后的数值维度）
   - AI 生成的综合评估（result.summary）
3. 加载中显示 spinner
4. 加载失败显示错误信息和返回链接

雷达图组件 ResultRadar.tsx：
- 使用纯 SVG 绘制（不依赖第三方图表库）
- 接收 data: {dimension, score, fullMark?}[] 
- 绘制多层网格、数据区域（半透明填充）、维度标签
- 下方显示各维度分数列表（按分数段着色）
```

### 阶段 6：成长画像页面

#### AI 提示词

```
请创建成长画像页面 src/app/assessment/profile/page.tsx：

功能要求：
1. 调用 fetchGrowthProfile() 获取所有已完成测评的聚合数据
2. 页面结构：
   a. 顶部概览卡片（蓝色渐变背景）：
      - 综合得分（所有测评平均分）
      - 完成进度（N/5）
      - 各测评得分列表
   b. 各测评综合得分进度条（带颜色编码）
   c. 每项已完成测评的详细卡片：
      - 雷达图
      - 突出维度标签（top 3，按分数着色）
      - 评估总结
      - 霍兰德代码（如有）
   d. 未完成提示（如果还有测评未完成）
3. 分数颜色编码：>=80 绿色，>=60 蓝色，>=40 黄色，<40 红色
4. 返回测评中心按钮

后端 API：GET /assessments/growth-profile
返回格式：
{
  completed_count: number,
  total_count: number,
  assessments: { [type]: { id, type, result_data, summary, completed_at } },
  overall_scores: { [type]: number },
  overall_avg: number
}
```

### 阶段 7：布局与导航

#### AI 提示词

```
请创建测评模块布局 src/app/assessment/layout.tsx：

功能要求：
1. 检测当前路由，决定是否显示公共头部：
   - 答题页（/assessment/holland 等）→ 不显示公共头部（答题页有自己的头部）
   - 结果页（/assessment/result/xxx）→ 不显示公共头部
   - 成长画像页（/assessment/profile）→ 不显示公共头部
   - 测评中心（/assessment）→ 显示公共头部
2. 公共头部包含：
   - 左侧："智能测评中心" 标题 + "发现自我，规划未来" 副标题
   - 点击标题导航回 /assessment
3. URL slug 识别列表：['holland', 'ability', 'values', 'learning-habit', 'readiness']
```

### 阶段 8：启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000 查看效果。

---

## 五、完整用户流程

```
用户打开首页 (/)
  → 重定向到测评中心 (/assessment)
  → 看到 5 张测评卡片 + "成长画像"按钮
  
点击"开始测评"
  → 导航到答题页 (/assessment/holland)
  → 自动调用 start API 获取题目
  → 逐题作答，每题选择后自动提交并跳转下一题
  → 最后一题提交后自动调用 submit API
  → 导航到结果页 (/assessment/result/{id})
  → 查看雷达图、霍兰德代码、AI 总结

完成所有 5 项测评后：
  → 点击"查看成长画像"
  → 导航到成长画像页 (/assessment/profile)
  → 查看综合得分、各测评进度、详细维度分析
```

---

## 六、常见坑与解决方案

### 6.1 SQLite 不支持 UUID 类型

**错误**：`ProgrammingError: Error binding parameter: type 'UUID' is not supported`

**解决**：所有主键使用 `String(36)` + `default=lambda: str(uuid4())`，创建记录时用 `id=str(uuid4())` 而非 `id=uuid4()`。

### 6.2 SQLite 不支持 Enum 类型

**错误**：`NoSuchModuleError` 或类型不匹配

**解决**：使用 `Column(String(20))` 代替 `Column(Enum(...))`。

### 6.3 测评提交 500 错误（唯一约束冲突）

**原因**：`AssessmentResult.assessment_id` 有 `unique=True` 约束，重新做测评时旧结果未清理。

**解决**：
1. `start_assessment` 中重新开始时删除旧的回答和结果
2. `submit_assessment` 中先查询是否已有结果，有则更新、无则新建

### 6.4 霍兰德代码为空

**原因**：`submit_assessment` 中为题目生成了新的随机 UUID，与回答中的 `question_id` 无法匹配。

**解决**：`calculate_result` 函数按回答顺序（即题目顺序）直接从 `DEFAULT_QUESTIONS` 获取维度，不依赖 ID 匹配。同时对回答按 `created_at` 排序。

### 6.5 Next.js SWC 二进制错误

**错误**：`Failed to load SWC binary: not a valid Win32 application`

**原因**：Next.js 14.x 不兼容 Node.js v24+。

**解决**：`npm install next@latest` 升级到最新版。

### 6.6 前端按钮点击无反应

**常见原因**：
1. 点击后直接调 API 但没有路由导航 → 使用 `router.push()`
2. API 拦截器在 401 时重定向到登录页 → 移除自动重定向
3. Layout 路由匹配不包含 `learning-habit` → 更新 URL_SLUGS 列表

---

## 七、一键启动命令

### Windows PowerShell

```powershell
# 终端 1：启动后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2：启动前端
cd frontend
npm install
npm run dev
```

### 验证

- 后端 API 文档：http://localhost:8000/docs
- 前端页面：http://localhost:3000
- 健康检查：http://localhost:8000/health

---

## 八、完整 AI 提示词（一次性生成）

> 以下提示词适用于 Qoder / Trae / Claude Code 等 AI 编程工具，可一次性生成完整项目。

### 8.1 后端完整提示词

```
请帮我从零创建一个 FastAPI 后端项目，项目名：大学生成长赋能平台后端。

技术栈：FastAPI + SQLAlchemy 2.0 (异步) + SQLite (aiosqlite) + pydantic-settings

项目结构：
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI入口，CORS配置(允许localhost:3000)，注册路由/api/v1/assessments
│   ├── config.py          # pydantic-settings, 从.env读取: DATABASE_URL(sqlite+aiosqlite:///./college_growth.db), JWT_SECRET_KEY, AI_API_KEY, CORS_ORIGINS
│   ├── database.py        # create_async_engine, SQLite需check_same_thread=False, async_session, get_db依赖
│   ├── dependencies.py    # HTTPBearer(auto_error=False), 开发模式自动创建默认用户(无需真实认证)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py        # users表: id(String36), email, nickname, password_hash, role(String20), is_active, created_at
│   │   └── assessment.py  # 5张表: assessments, assessment_questions, assessment_responses, assessment_results(assessment_id unique), assessment_histories
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py      # 调用OpenAI API分析测评结果(API_KEY为空时跳过)
│   │   └── assessment_service.py  # 核心业务逻辑
│   └── api/v1/assessment/
│       ├── __init__.py     # 所有API路由
├── requirements.txt
└── .env

核心业务逻辑 (assessment_service.py)：

1. 题库(DEFAULT_QUESTIONS)包含5种测评共70道题：
   - 霍兰德(holland): 18题, 6维度(R/I/A/S/E/C)各3题, 5级量表(非常不同意→非常同意)
   - 能力自评(ability): 16题, 8维度各2题
   - 价值观(values): 8题, 8维度各1题
   - 学习习惯(learning_habit): 14题, 7维度各2题
   - 准备度(readiness): 14题, 7维度各2题

2. API端点：
   GET  /api/v1/assessments                    → 获取所有测评状态
   GET  /api/v1/assessments/growth-profile     → 成长画像(必须在/{type}路由之前定义)
   POST /api/v1/assessments/{type}/start       → 开始测评(重新开始时清理旧数据)
   POST /api/v1/assessments/{id}/answer        → 提交单个答案
   POST /api/v1/assessments/{id}/submit        → 提交整个测评(幂等:已有结果则更新)
   GET  /api/v1/assessments/{id}/result        → 获取结果

3. 分数计算(calculate_result)：
   - 按回答顺序(from created_at排序)匹配题库维度，不依赖question_id
   - 每维度取均值×20转为0-100分
   - 霍兰德:取top3维度生成代码(如"EIA")和描述

4. 成长画像(get_growth_profile)：
   - 聚合所有已完成测评的结果
   - 计算各测评综合得分(维度均值)和总体平均分

关键注意事项：
- 所有UUID主键用 String(36) + str(uuid4())，不要用 PostgreSQL UUID 类型
- 不要用 Enum 类型，用 String(20)
- AssessmentResult 的 assessment_id 有 unique 约束，重新测评时需清理旧数据
- submit_assessment 需幂等处理(先查后建)
```

### 8.2 前端完整提示词

```
请帮我从零创建一个 Next.js 前端项目，项目名：大学生成长赋能平台前端。

技术栈：Next.js 16+ (App Router) + TypeScript + Tailwind CSS + Zustand + Axios

初始化步骤：
1. npx create-next-app@latest frontend (选TypeScript, App Router, Tailwind, src目录)
2. cd frontend && npm install zustand axios
3. npm install next@latest (确保兼容Node.js最新版)

项目结构：
frontend/src/
├── app/
│   ├── layout.tsx              # 根布局
│   ├── page.tsx                # 首页(重定向到/assessment)
│   ├── globals.css             # Tailwind指令 + 中文字体
│   └── assessment/
│       ├── layout.tsx          # 测评布局(答题页/结果页/画像页不显示公共头部)
│       ├── page.tsx            # 测评中心(5张卡片+成长画像入口)
│       ├── [type]/page.tsx     # 答题页(动态路由: holland/ability/values/learning-habit/readiness)
│       ├── result/[id]/page.tsx # 结果页(雷达图+霍兰德代码+AI总结)
│       └── profile/page.tsx    # 成长画像(综合得分+进度条+各测评详情)
├── components/assessment/
│   ├── LikertScale.tsx         # 李克特5级量表(5个按钮横排)
│   ├── ProgressBar.tsx         # 进度条(第N题/共M题)
│   └── ResultRadar.tsx         # SVG雷达图(纯SVG,无第三方依赖)
├── store/assessmentStore.ts    # Zustand状态管理
├── lib/api.ts                  # Axios封装(baseURL=/api/v1, 响应拦截返回response.data)
└── types/assessment.ts         # TypeScript类型 + 常量(LABELS/DESCRIPTIONS/ICONS)

核心页面逻辑：

1. 测评中心(page.tsx)：
   - 5张卡片网格布局, 每张显示图标+标题+状态+操作按钮
   - 点击按钮→router.push导航到答题页
   - 右上角"成长画像"按钮(显示完成进度N/5)

2. 答题页([type]/page.tsx)：
   - 自动调用startAssessment开始测评
   - 显示进度条+题目+李克特量表
   - 选择答案→自动提交→下一题(最后一题自动submit→跳转结果页)
   - URL映射: learning-habit→learning_habit

3. 结果页(result/[id]/page.tsx)：
   - 获取并展示: 霍兰德代码+雷达图+AI总结
   - 雷达图用纯SVG绘制

4. 成长画像(profile/page.tsx)：
   - 调用GET /assessments/growth-profile
   - 顶部渐变卡片(综合得分+完成进度)
   - 各测评得分进度条
   - 各测评详情卡片(雷达图+突出维度+总结)

5. API封装(lib/api.ts)：
   - baseURL: http://localhost:8000/api/v1
   - 响应拦截器直接返回response.data
   - 不要401自动跳转登录页

6. 状态管理(Zustand)：
   - statusMap: 各测评状态
   - currentAssessment/currentQuestions/currentIndex: 当前答题状态
   - growthProfile: 成长画像数据
   - 方法: fetchStatus, startAssessment, submitAnswer, submitAssessment, fetchResult, fetchGrowthProfile

注意事项：
- Next.js版本必须>=15以兼容Node.js v24+
- 所有页面使用'use client'指令
- Tailwind CSS 配置扫描 src/ 下所有文件
- 使用中文界面
```

---

## 九、扩展建议

| 方向 | 说明 |
|------|------|
| 用户认证 | 接入 JWT 登录注册，替换开发模式默认用户 |
| AI 分析 | 配置 AI_API_KEY 启用 AI 生成个性化分析报告 |
| 数据持久化 | 迁移到 PostgreSQL 支持生产环境 |
| 导出报告 | 使用 openpyxl 生成 Excel 测评报告 |
| 移动端适配 | Tailwind 已支持响应式，可进一步优化 |
