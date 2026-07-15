# MVP 开发任务规划文档 — 代码开发框架版

> **技术栈**：前端 — Next.js 14+ (App Router) + Tailwind CSS + Shadcn/ui + Zustand/React Query  
> **后端**：FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL  
> **AI 接入**：OpenAI/Claude API | **认证**：JWT + OAuth2  
> **部署**：Docker + Nginx  
> **文档版本**：v2.0（代码开发框架版）

---

## 一、项目概述

大学生成长赋能平台，涵盖从「成长档案 → 智能测评 → 成长画像 → 方向分析 → 规划生成 → 任务管理 → 智能问答 → 内容生成」的全链路闭环，以 AI 为核心驱动，帮助学生实现个性化成长。

---

## 二、项目根目录结构

```
college-growth-platform/
├── backend/                          # FastAPI 后端项目
│   ├── alembic/                      # 数据库迁移
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 全局配置
│   │   ├── database.py               # 数据库连接
│   │   ├── dependencies.py           # 依赖注入（认证、分页等）
│   │   ├── models/                   # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── profile.py            # 个人成长档案模型
│   │   │   ├── assessment.py         # 智能测评模型
│   │   │   ├── portrait.py           # 成长画像模型
│   │   │   ├── direction.py          # 方向分析模型
│   │   │   ├── plan.py               # 规划生成模型
│   │   │   ├── task.py               # 任务管理模型
│   │   │   ├── qa.py                 # 智能问答模型
│   │   │   └── content.py            # 内容生成模型
│   │   ├── schemas/                  # Pydantic 数据模式
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── assessment.py
│   │   │   ├── portrait.py
│   │   │   ├── direction.py
│   │   │   ├── plan.py
│   │   │   ├── task.py
│   │   │   ├── qa.py
│   │   │   └── content.py
│   │   ├── api/                      # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py           # 认证相关
│   │   │   │   ├── users.py          # 用户管理
│   │   │   │   ├── profile/          # 模块1: 个人成长档案
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── basic_info.py
│   │   │   │   │   ├── academics.py
│   │   │   │   │   ├── interests.py
│   │   │   │   │   ├── projects.py
│   │   │   │   │   ├── internships.py
│   │   │   │   │   ├── certificates.py
│   │   │   │   │   ├── portfolio.py
│   │   │   │   │   ├── goals.py
│   │   │   │   │   └── authorization.py
│   │   │   │   ├── assessment/       # 模块2: 智能测评
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── holland.py
│   │   │   │   │   ├── ability.py
│   │   │   │   │   ├── values.py
│   │   │   │   │   ├── learning_habit.py
│   │   │   │   │   └── readiness.py
│   │   │   │   ├── portrait/         # 模块3: 成长画像
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── overview.py
│   │   │   │   │   ├── academics.py
│   │   │   │   │   ├── ability.py
│   │   │   │   │   ├── practice.py
│   │   │   │   │   ├── career.py
│   │   │   │   │   └── export.py
│   │   │   │   ├── direction/        # 模块4: 方向分析
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── employment.py
│   │   │   │   │   ├── graduate.py
│   │   │   │   │   ├── entrepreneurship.py
│   │   │   │   │   ├── comparison.py
│   │   │   │   │   └── matching.py
│   │   │   │   ├── plan/             # 模块5: 规划生成
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── overall.py
│   │   │   │   │   ├── term_plan.py
│   │   │   │   │   ├── milestone.py
│   │   │   │   │   ├── alternative.py
│   │   │   │   │   └── adjustment.py
│   │   │   │   ├── tasks/            # 模块6: 任务管理
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── tasks.py
│   │   │   │   │   ├── board.py
│   │   │   │   │   ├── review.py
│   │   │   │   │   └── evaluation.py
│   │   │   │   ├── qa/               # 模块7: 智能问答
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── chat.py
│   │   │   │   │   ├── session.py
│   │   │   │   │   └── knowledge.py
│   │   │   │   ├── content/          # 模块8: 内容生成
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── report.py
│   │   │   │   │   ├── resume.py
│   │   │   │   │   ├── statement.py
│   │   │   │   │   ├── story.py
│   │   │   │   │   ├── script.py
│   │   │   │   │   ├── poster.py
│   │   │   │   │   └── summary.py
│   │   │   │   └── upload.py         # 文件上传通用接口
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── assessment_service.py
│   │   │   ├── portrait_service.py
│   │   │   ├── direction_service.py
│   │   │   ├── plan_service.py
│   │   │   ├── task_service.py
│   │   │   ├── qa_service.py
│   │   │   ├── content_service.py
│   │   │   └── ai_service.py         # AI 调用统一封装
│   │   ├── utils/                    # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── file_handler.py
│   │   │   ├── excel_handler.py
│   │   │   └── auth_utils.py
│   │   └── middleware/               # 中间件
│   │       ├── __init__.py
│   │       ├── cors.py
│   │       └── rate_limit.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                         # Next.js 前端项目
│   ├── src/
│   │   ├── app/                      # App Router 页面
│   │   │   ├── layout.tsx            # 根布局
│   │   │   ├── page.tsx              # 首页/登录页
│   │   │   ├── auth/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── dashboard/            # 仪表盘
│   │   │   │   └── page.tsx
│   │   │   ├── profile/              # 模块1: 个人成长档案
│   │   │   │   ├── page.tsx
│   │   │   │   ├── basic-info/page.tsx
│   │   │   │   ├── academics/page.tsx
│   │   │   │   ├── interests/page.tsx
│   │   │   │   ├── projects/page.tsx
│   │   │   │   ├── internships/page.tsx
│   │   │   │   ├── certificates/page.tsx
│   │   │   │   ├── portfolio/page.tsx
│   │   │   │   ├── goals/page.tsx
│   │   │   │   └── authorization/page.tsx
│   │   │   ├── assessment/           # 模块2: 智能测评
│   │   │   │   ├── page.tsx          # 测评中心
│   │   │   │   ├── holland/page.tsx
│   │   │   │   ├── ability/page.tsx
│   │   │   │   ├── values/page.tsx
│   │   │   │   ├── learning-habit/page.tsx
│   │   │   │   └── readiness/page.tsx
│   │   │   ├── portrait/             # 模块3: 成长画像
│   │   │   │   ├── page.tsx          # 画像总览仪表盘
│   │   │   │   ├── academics/page.tsx
│   │   │   │   ├── ability/page.tsx
│   │   │   │   ├── practice/page.tsx
│   │   │   │   ├── career/page.tsx
│   │   │   │   └── export/page.tsx
│   │   │   ├── direction/            # 模块4: 方向分析
│   │   │   │   ├── page.tsx          # 方向分析主页
│   │   │   │   ├── employment/page.tsx
│   │   │   │   ├── graduate/page.tsx
│   │   │   │   ├── entrepreneurship/page.tsx
│   │   │   │   └── comparison/page.tsx
│   │   │   ├── plan/                 # 模块5: 规划生成
│   │   │   │   ├── page.tsx          # 规划总览
│   │   │   │   ├── overall/page.tsx
│   │   │   │   ├── term/page.tsx
│   │   │   │   ├── milestone/page.tsx
│   │   │   │   └── adjustment/page.tsx
│   │   │   ├── tasks/                # 模块6: 任务管理
│   │   │   │   ├── page.tsx          # 任务看板
│   │   │   │   ├── create/page.tsx
│   │   │   │   ├── [id]/page.tsx     # 任务详情
│   │   │   │   └── review/page.tsx   # 任务复盘
│   │   │   ├── qa/                   # 模块7: 智能问答
│   │   │   │   ├── page.tsx          # 问答主页
│   │   │   │   └── session/[id]/page.tsx
│   │   │   └── content/              # 模块8: 内容生成
│   │   │       ├── page.tsx          # 内容生成中心
│   │   │       ├── report/page.tsx
│   │   │       ├── resume/page.tsx
│   │   │       ├── statement/page.tsx
│   │   │       ├── story/page.tsx
│   │   │       ├── script/page.tsx
│   │   │       ├── poster/page.tsx
│   │   │       └── summary/page.tsx
│   │   ├── components/               # 共享组件
│   │   │   ├── ui/                   # Shadcn/ui 组件
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Navbar.tsx
│   │   │   │   └── AppShell.tsx
│   │   │   ├── charts/               # 图表组件
│   │   │   │   ├── RadarChart.tsx
│   │   │   │   ├── LineChart.tsx
│   │   │   │   ├── BarChart.tsx
│   │   │   │   └── GanttChart.tsx
│   │   │   ├── common/
│   │   │   │   ├── FileUpload.tsx
│   │   │   │   ├── RichTextEditor.tsx
│   │   │   │   ├── TagInput.tsx
│   │   │   │   ├── ProgressSteps.tsx
│   │   │   │   └── LoadingState.tsx
│   │   │   └── profile/              # 模块1 专用组件
│   │   │       ├── BasicInfoForm.tsx
│   │   │       ├── AcademicForm.tsx
│   │   │       ├── InterestTags.tsx
│   │   │       ├── ProjectCard.tsx
│   │   │       └── AuthorizationPanel.tsx
│   │   │   ├── assessment/           # 模块2 专用组件
│   │   │   │   ├── LikertScale.tsx
│   │   │   │   ├── ProgressBar.tsx
│   │   │   │   └── ResultRadar.tsx
│   │   │   ├── portrait/             # 模块3 专用组件
│   │   │   │   ├── ScoreCard.tsx
│   │   │   │   ├── TrendChart.tsx
│   │   │   │   └── ComparisonBar.tsx
│   │   │   ├── direction/            # 模块4 专用组件
│   │   │   │   ├── MatchCard.tsx
│   │   │   │   ├── ComparisonTable.tsx
│   │   │   │   └── GapAnalysis.tsx
│   │   │   ├── plan/                 # 模块5 专用组件
│   │   │   │   ├── TimelineView.tsx
│   │   │   │   ├── MilestoneNode.tsx
│   │   │   │   └── PlanAdjuster.tsx
│   │   │   ├── tasks/                # 模块6 专用组件
│   │   │   │   ├── KanbanBoard.tsx
│   │   │   │   ├── TaskCard.tsx
│   │   │   │   ├── CalendarView.tsx
│   │   │   │   └── PomodoroTimer.tsx
│   │   │   ├── qa/                   # 模块7 专用组件
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   └── KnowledgeSource.tsx
│   │   │   └── content/              # 模块8 专用组件
│   │   │       ├── ContentEditor.tsx
│   │   │       ├── TemplateSelector.tsx
│   │   │       └── ExportPanel.tsx
│   │   ├── hooks/                    # 自定义 Hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useProfile.ts
│   │   │   ├── useAssessment.ts
│   │   │   ├── usePortrait.ts
│   │   │   ├── useDirection.ts
│   │   │   ├── usePlan.ts
│   │   │   ├── useTask.ts
│   │   │   ├── useQA.ts
│   │   │   └── useContent.ts
│   │   ├── lib/                      # 工具库
│   │   │   ├── api.ts                # Axios 实例 + 请求封装
│   │   │   ├── utils.ts
│   │   │   ├── constants.ts
│   │   │   └── validators.ts
│   │   ├── store/                    # Zustand 状态管理
│   │   │   ├── authStore.ts
│   │   │   ├── profileStore.ts
│   │   │   ├── assessmentStore.ts
│   │   │   ├── taskStore.ts
│   │   │   └── qaStore.ts
│   │   └── types/                    # TypeScript 类型
│   │       ├── user.ts
│   │       ├── profile.ts
│   │       ├── assessment.ts
│   │       ├── portrait.ts
│   │       ├── direction.ts
│   │       ├── plan.ts
│   │       ├── task.ts
│   │       ├── qa.ts
│   │       └── content.ts
│   ├── public/                       # 静态资源
│   │   └── uploads/
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── package.json
│   ├── Dockerfile
│   └── .env.local.example
├── docker-compose.yml                # Docker 编排
├── .gitignore
└── README.md
```

---

## 三、数据库模型详细定义

### 3.1 通用说明

- 所有模型继承 `Base`（SQLAlchemy declarative base）
- 统一包含字段：`id` (UUID, PK), `created_at`, `updated_at`
- 使用 `asyncpg` 作为 PostgreSQL 异步驱动
- JSON 字段用于存储动态结构数据

### 3.2 用户与认证模块

```python
# backend/app/models/user.py
class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(Enum("student", "teacher", "admin"), default="student")
    is_active = Column(Boolean, default=True)
    oauth_provider = Column(String(50), nullable=True)  # wechat, github, etc.
    oauth_id = Column(String(255), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    profile = relationship("Profile", back_populates="user", uselist=False)
    assessments = relationship("Assessment", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    qa_sessions = relationship("QASession", back_populates="user")
```

### 3.3 模块1：个人成长档案模型

```python
# backend/app/models/profile.py

# --- 基本信息 ---
class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), unique=True, nullable=False)
    real_name = Column(String(50), nullable=True)
    gender = Column(Enum("male", "female", "other"), nullable=True)
    birth_date = Column(Date, nullable=True)
    birthplace = Column(String(100), nullable=True)
    political_status = Column(String(50), nullable=True)  # 政治面貌
    bio = Column(Text, nullable=True)  # 个人简介（富文本 HTML）
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")
    academics = relationship("AcademicInfo", back_populates="profile", uselist=False)
    interests = relationship("InterestTag", back_populates="profile")
    projects = relationship("ProjectExperience", back_populates="profile")
    internships = relationship("Internship", back_populates="profile")
    certificates = relationship("Certificate", back_populates="profile")
    skills = relationship("Skill", back_populates="profile")
    portfolio_items = relationship("PortfolioItem", back_populates="profile")
    goals = relationship("GoalIntention", back_populates="profile")

# --- 学业信息 ---
class AcademicInfo(Base):
    __tablename__ = "academic_info"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), unique=True, nullable=False)
    school = Column(String(100), nullable=False)
    college = Column(String(100), nullable=True)  # 学院
    major = Column(String(100), nullable=False)
    grade = Column(String(20), nullable=True)  # 年级
    class_name = Column(String(50), nullable=True)
    student_id = Column(String(30), nullable=True)
    enrollment_year = Column(Integer, nullable=False)
    education_system = Column(Integer, default=4)  # 4年/5年/2年
    gpa = Column(Float, nullable=True)
    gpa_total = Column(Float, nullable=True)  # 满分
    rank_percent = Column(Float, nullable=True)  # 排名百分比
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    profile = relationship("Profile", back_populates="academics")
    courses = relationship("Course", back_populates="academic_info")

class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID, primary_key=True, default=uuid4)
    academic_info_id = Column(UUID, ForeignKey("academic_info.id"), nullable=False)
    name = Column(String(100), nullable=False)
    score = Column(Float, nullable=True)
    credit = Column(Float, nullable=False)
    semester = Column(String(20), nullable=True)  # "2024-2025-1"
    course_type = Column(Enum("required", "elective", "public"), default="required")
    is_current = Column(Boolean, default=False)  # 是否当前学期课程
    created_at = Column(DateTime, default=func.now())

    academic_info = relationship("AcademicInfo", back_populates="courses")

# --- 兴趣标签 ---
class InterestCategory(Base):
    __tablename__ = "interest_categories"
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(50), nullable=False)  # 大类：技术/艺术/体育...
    sort_order = Column(Integer, default=0)
    tags = relationship("InterestTag", back_populates="category")

class InterestTag(Base):
    __tablename__ = "interest_tags"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), nullable=False)
    category_id = Column(UUID, ForeignKey("interest_categories.id"), nullable=True)
    name = Column(String(50), nullable=False)
    weight = Column(Integer, default=5)  # 1-10 优先级权重
    source = Column(Enum("manual", "assessment"), default="manual")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    profile = relationship("Profile", back_populates="interests")
    category = relationship("InterestCategory", back_populates="tags")

# --- 项目/竞赛/科研 ---
class ProjectExperience(Base):
    __tablename__ = "project_experiences"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), nullable=False)
    title = Column(String(200), nullable=False)
    role = Column(Enum("leader", "core_member", "participant"), default="participant")
    field = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)  # Markdown
    achievements = Column(JSON, nullable=True)  # 成果展示：[{type: "image|link|doc", url: "..."}]
    award_level = Column(Enum("school", "provincial", "national", "international"), nullable=True)
    evidence_files = Column(JSON, nullable=True)  # 证明材料URL列表
    project_type = Column(Enum("competition", "research", "project"), default="project")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    profile = relationship("Profile", back_populates="projects")

# --- 实习/实践 ---
class Internship(Base):
    __tablename__ = "internships"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), nullable=False)
    company = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    certificate_files = Column(JSON, nullable=True)
    self_evaluation = Column(Text, nullable=True)
    mentor_evaluation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    profile = relationship("Profile", back_populates="internships")

# --- 证书/技能 ---
class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), nullable=False)
    name = Column(String(200), nullable=False)
    issuer = Column(String(200), nullable=True)
    obtain_date = Column(Date, nullable=True)
    file_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    profile = relationship("Profile", back_populates="certificates")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), nullable=False)
    name = Column(String(100), nullable=False)
    proficiency = Column(Enum("beginner", "learning", "mastering", "expert"), default="beginner")
    category = Column(Enum("hard", "soft"), default="hard")
    created_at = Column(DateTime, default=func.now())

    profile = relationship("Profile", back_populates="skills")

# --- 作品集 ---
class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(Enum("code", "design", "writing", "video", "other"), default="other")
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    link_url = Column(String(500), nullable=True)
    creation_date = Column(Date, nullable=True)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    profile = relationship("Profile", back_populates="portfolio_items")

# --- 目标意向 ---
class GoalIntention(Base):
    __tablename__ = "goal_intentions"
    id = Column(UUID, primary_key=True, default=uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id"), nullable=False)
    intention_type = Column(Enum("employment", "graduate", "study_abroad", "entrepreneurship", "civil_service"), nullable=False)
    target_content = Column(JSON, nullable=True)  # 目标详情：{industry/job/school/major...}
    priority = Column(Integer, default=0)  # 排序优先级
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    profile = relationship("Profile", back_populates="goals")
    change_history = relationship("GoalChangeLog", back_populates="goal")

class GoalChangeLog(Base):
    __tablename__ = "goal_change_logs"
    id = Column(UUID, primary_key=True, default=uuid4)
    goal_id = Column(UUID, ForeignKey("goal_intentions.id"), nullable=False)
    old_content = Column(JSON, nullable=True)
    new_content = Column(JSON, nullable=True)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    goal = relationship("GoalIntention", back_populates="change_history")

# --- 信息授权 ---
class DataAuthorization(Base):
    __tablename__ = "data_authorizations"
    id = Column(UUID, primary_key=True, default=uuid4)
    owner_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    grantee_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    auth_code = Column(String(64), unique=True, nullable=False)
    modules = Column(JSON, nullable=False)  # 可见模块列表：["basic_info", "academics", ...]
    expire_at = Column(DateTime, nullable=True)  # null 表示长期
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    last_view_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
```

### 3.4 模块2：智能测评模型

```python
# backend/app/models/assessment.py

# --- 测评问卷 ---
class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    type = Column(Enum("holland", "ability", "values", "learning_habit", "readiness"), nullable=False)
    status = Column(Enum("not_started", "in_progress", "completed"), default="not_started")
    current_question = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="assessments")
    responses = relationship("AssessmentResponse", back_populates="assessment")
    results = relationship("AssessmentResult", back_populates="assessment", uselist=False)

# --- 测评题目 ---
class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id = Column(UUID, primary_key=True, default=uuid4)
    type = Column(Enum("holland", "ability", "values", "learning_habit", "readiness"), nullable=False)
    dimension = Column(String(50), nullable=True)  # 所属维度
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # [{label: "非常同意", value: 5}, ...]
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

# --- 测评答题记录 ---
class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"
    id = Column(UUID, primary_key=True, default=uuid4)
    assessment_id = Column(UUID, ForeignKey("assessments.id"), nullable=False)
    question_id = Column(UUID, ForeignKey("assessment_questions.id"), nullable=False)
    answer_value = Column(JSON, nullable=False)  # 答案（支持单选/多选/排序）
    created_at = Column(DateTime, default=func.now())

    assessment = relationship("Assessment", back_populates="responses")
    question = relationship("AssessmentQuestion")

# --- 测评结果 ---
class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    id = Column(UUID, primary_key=True, default=uuid4)
    assessment_id = Column(UUID, ForeignKey("assessments.id"), unique=True, nullable=False)
    type = Column(Enum("holland", "ability", "values", "learning_habit", "readiness"), nullable=False)
    result_data = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    assessment = relationship("Assessment", back_populates="results")

# --- 测评历史（快照，用于趋势分析） ---
class AssessmentHistory(Base):
    __tablename__ = "assessment_histories"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    type = Column(Enum("holland", "ability", "values", "learning_habit", "readiness"), nullable=False)
    result_snapshot = Column(JSON, nullable=False)
    version = Column(Integer, default=1)  # 第几次测评
    created_at = Column(DateTime, default=func.now())
```

### 3.5 模块3：成长画像模型

```python
# backend/app/models/portrait.py

class Portrait(Base):
    __tablename__ = "portraits"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), unique=True, nullable=False)
    # 各维度得分（自动计算）
    academic_score = Column(Float, nullable=True)        # 专业知识维度
    ability_score = Column(JSON, nullable=True)           # 通用能力维度各分项
    practice_score = Column(JSON, nullable=True)          # 实践能力维度
    career_readiness = Column(JSON, nullable=True)        # 职业准备度
    interest_match = Column(JSON, nullable=True)          # 兴趣与目标分析
    goal_clarity = Column(JSON, nullable=True)            # 目标清晰度与执行力
    overall_score = Column(Float, nullable=True)          # 综合评分
    last_calculated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    history = relationship("PortraitHistory", back_populates="portrait")

class PortraitHistory(Base):
    __tablename__ = "portrait_histories"
    id = Column(UUID, primary_key=True, default=uuid4)
    portrait_id = Column(UUID, ForeignKey("portraits.id"), nullable=False)
    snapshot = Column(JSON, nullable=False)                # 完整画像快照
    semester = Column(String(20), nullable=False)          # 学期标识：2024-2025-1
    created_at = Column(DateTime, default=func.now())

    portrait = relationship("Portrait", back_populates="history")
```

### 3.6 模块4：方向分析模型

```python
# backend/app/models/direction.py

class DirectionAnalysis(Base):
    __tablename__ = "direction_analyses"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    type = Column(Enum("employment", "graduate", "entrepreneurship"), nullable=False)
    result_data = Column(JSON, nullable=False)             # AI 分析结果详情
    match_score = Column(Float, nullable=True)             # 总体匹配度
    confidence = Column(Enum("high", "medium", "low"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    comparisons = relationship("DirectionComparison", foreign_keys="DirectionComparison.user_id")

class DirectionComparison(Base):
    __tablename__ = "direction_comparisons"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    comparison_data = Column(JSON, nullable=False)         # 多方向对比数据
    ai_suggestion = Column(Text, nullable=True)            # AI 综合建议
    created_at = Column(DateTime, default=func.now())
```

### 3.7 模块5：规划生成模型

```python
# backend/app/models/plan.py

class GrowthPlan(Base):
    __tablename__ = "growth_plans"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=True)
    plan_type = Column(Enum("overall", "yearly", "semester", "monthly", "weekly"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    content = Column(JSON, nullable=False)                 # 规划内容（目标 + 任务 + 里程碑）
    status = Column(Enum("active", "completed", "archived"), default="active")
    is_primary = Column(Boolean, default=False)            # 是否是主规划
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    milestones = relationship("Milestone", back_populates="plan")
    adjustments = relationship("PlanAdjustment", back_populates="plan")

class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(UUID, primary_key=True, default=uuid4)
    plan_id = Column(UUID, ForeignKey("growth_plans.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=False)
    status = Column(Enum("pending", "in_progress", "completed", "delayed"), default="pending")
    is_key_milestone = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    plan = relationship("GrowthPlan", back_populates="milestones")

class PlanAdjustment(Base):
    __tablename__ = "plan_adjustments"
    id = Column(UUID, primary_key=True, default=uuid4)
    plan_id = Column(UUID, ForeignKey("growth_plans.id"), nullable=False)
    adjustment_type = Column(Enum("auto", "manual"), nullable=False)
    reason = Column(String(500), nullable=True)
    changes = Column(JSON, nullable=False)                 # 变更内容详情
    created_at = Column(DateTime, default=func.now())

    plan = relationship("GrowthPlan", back_populates="adjustments")
```

### 3.8 模块6：任务管理模型

```python
# backend/app/models/task.py

class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    plan_id = Column(UUID, ForeignKey("growth_plans.id"), nullable=True)  # 所属规划
    parent_task_id = Column(UUID, ForeignKey("tasks.id"), nullable=True)  # 父任务
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum("todo", "in_progress", "completed", "delayed"), default="todo")
    priority = Column(Enum("p0", "p1", "p2"), default="p2")
    progress = Column(Integer, default=0)                  # 0-100
    tag = Column(Enum("academic", "practice", "ability", "other"), default="other")
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tasks")
    parent = relationship("Task", remote_side=[id], backref="subtasks")
    deliverables = relationship("TaskDeliverable", back_populates="task")
    evaluations = relationship("TaskEvaluation", back_populates="task")

class TaskDeliverable(Base):
    __tablename__ = "task_deliverables"
    id = Column(UUID, primary_key=True, default=uuid4)
    task_id = Column(UUID, ForeignKey("tasks.id"), nullable=False)
    file_url = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    task = relationship("Task", back_populates="deliverables")

class TaskEvaluation(Base):
    __tablename__ = "task_evaluations"
    id = Column(UUID, primary_key=True, default=uuid4)
    task_id = Column(UUID, ForeignKey("tasks.id"), nullable=False)
    evaluator_type = Column(Enum("ai", "teacher", "self"), nullable=False)
    evaluator_id = Column(UUID, nullable=True)
    score = Column(Integer, nullable=True)                 # 1-100
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    task = relationship("Task", back_populates="evaluations")

class TaskReview(Base):
    __tablename__ = "task_reviews"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    review_type = Column(Enum("weekly", "monthly"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    stats = Column(JSON, nullable=False)                   # 完成率/耗时分布/质量评分
    self_evaluation = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
```

### 3.9 模块7：智能问答模型

```python
# backend/app/models/qa.py

class QASession(Base):
    __tablename__ = "qa_sessions"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    category = Column(Enum("study", "employment", "graduate", "abroad", "entrepreneurship", "competition", "time_mgmt"), nullable=True)
    is_favorite = Column(Boolean, default=False)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="qa_sessions")
    messages = relationship("QAMessage", back_populates="session", order_by="QAMessage.created_at")

class QAMessage(Base):
    __tablename__ = "qa_messages"
    id = Column(UUID, primary_key=True, default=uuid4)
    session_id = Column(UUID, ForeignKey("qa_sessions.id"), nullable=False)
    role = Column(Enum("user", "assistant"), nullable=False)
    content = Column(Text, nullable=False)
    knowledge_sources = Column(JSON, nullable=True)        # 知识库引用来源
    created_at = Column(DateTime, default=func.now())

    session = relationship("QASession", back_populates="messages")
```

### 3.10 模块8：内容生成模型

```python
# backend/app/models/content.py

class GeneratedContent(Base):
    __tablename__ = "generated_contents"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(
        "growth_report", "resume", "statement",
        "story", "script", "poster", "annual_summary"
    ), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)                 # 生成的内容
    template_used = Column(String(50), nullable=True)
    status = Column(Enum("draft", "finalized"), default="draft")
    metadata = Column(JSON, nullable=True)                 # 生成参数等元数据
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    export_records = relationship("ContentExport", back_populates="content")

class ContentExport(Base):
    __tablename__ = "content_exports"
    id = Column(UUID, primary_key=True, default=uuid4)
    content_id = Column(UUID, ForeignKey("generated_contents.id"), nullable=False)
    format = Column(Enum("pdf", "word", "html"), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

    content = relationship("GeneratedContent", back_populates="export_records")
```

### 3.11 文件上传记录表

```python
# backend/app/models/__init__.py 中加入
class FileRecord(Base):
    __tablename__ = "file_records"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_type = Column(Enum("avatar", "evidence", "certificate", "deliverable", "other"), nullable=False)
    created_at = Column(DateTime, default=func.now())
```

---

## 四、API 端点详细定义

### 4.1 通用说明

- 基础路径：`/api/v1`
- 认证方式：`Bearer JWT Token`（除 auth 接口外）
- 响应格式统一：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "meta": { "page": 1, "page_size": 20, "total": 100 }
}
```

- 错误响应：

```json
{
  "code": 400,
  "message": "error description",
  "errors": { "field": ["error message"] }
}
```

### 4.2 用户认证 API

| 方法 | 路径 | 功能 | 请求体 |
|------|------|------|--------|
| POST | `/api/v1/auth/register` | 注册 | `{email, password, nickname}` |
| POST | `/api/v1/auth/login` | 登录 | `{email, password}` → 返回 JWT |
| POST | `/api/v1/auth/oauth` | OAuth 登录 | `{provider, code}` |
| POST | `/api/v1/auth/refresh` | 刷新 Token | `{refresh_token}` |
| GET | `/api/v1/auth/me` | 获取当前用户信息 | — |
| PUT | `/api/v1/auth/me` | 更新个人资料 | `{nickname, avatar_url}` |
| PUT | `/api/v1/auth/password` | 修改密码 | `{old_password, new_password}` |

### 4.3 模块1：个人成长档案 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/profile` | 获取个人档案概览 |
| PUT | `/api/v1/profile/basic-info` | 更新基本信息 |
| GET | `/api/v1/profile/academics` | 获取学业信息 |
| PUT | `/api/v1/profile/academics` | 更新学业信息 |
| POST | `/api/v1/profile/academics/courses` | 添加课程（支持批量） |
| DELETE | `/api/v1/profile/academics/courses/{id}` | 删除课程 |
| POST | `/api/v1/profile/academics/import-excel` | Excel 导入课程 |
| GET | `/api/v1/profile/interests` | 获取兴趣标签列表 |
| POST | `/api/v1/profile/interests` | 添加兴趣标签 |
| PUT | `/api/v1/profile/interests/{id}/weight` | 更新标签权重 |
| DELETE | `/api/v1/profile/interests/{id}` | 删除标签 |
| GET | `/api/v1/profile/interests/categories` | 获取预定义标签库 |
| GET | `/api/v1/profile/projects` | 获取项目/竞赛/科研列表 |
| POST | `/api/v1/profile/projects` | 添加项目经验 |
| PUT | `/api/v1/profile/projects/{id}` | 更新项目经验 |
| DELETE | `/api/v1/profile/projects/{id}` | 删除项目经验 |
| GET | `/api/v1/profile/internships` | 获取实习/实践列表 |
| POST | `/api/v1/profile/internships` | 添加实习经历 |
| PUT | `/api/v1/profile/internships/{id}` | 更新实习经历 |
| DELETE | `/api/v1/profile/internships/{id}` | 删除实习经历 |
| GET | `/api/v1/profile/certificates` | 获取证书列表 |
| POST | `/api/v1/profile/certificates` | 添加证书 |
| DELETE | `/api/v1/profile/certificates/{id}` | 删除证书 |
| GET | `/api/v1/profile/skills` | 获取技能列表 |
| POST | `/api/v1/profile/skills` | 添加技能 |
| PUT | `/api/v1/profile/skills/{id}` | 更新技能熟练度 |
| GET | `/api/v1/profile/portfolio` | 获取作品集列表 |
| POST | `/api/v1/profile/portfolio` | 添加作品 |
| PUT | `/api/v1/profile/portfolio/{id}` | 更新作品 |
| DELETE | `/api/v1/profile/portfolio/{id}` | 删除作品 |
| GET | `/api/v1/profile/goals` | 获取目标意向列表 |
| POST | `/api/v1/profile/goals` | 添加目标意向 |
| PUT | `/api/v1/profile/goals/{id}` | 更新目标意向 |
| GET | `/api/v1/profile/goals/{id}/history` | 获取目标变更历史 |
| GET | `/api/v1/profile/authorizations` | 获取授权列表 |
| POST | `/api/v1/profile/authorizations` | 创建授权码 |
| DELETE | `/api/v1/profile/authorizations/{id}` | 撤销授权 |
| POST | `/api/v1/profile/authorizations/verify` | 验证授权码访问 |

### 4.4 模块2：智能测评 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/assessments` | 获取所有测评状态 |
| POST | `/api/v1/assessments/{type}/start` | 开始某项测评 |
| GET | `/api/v1/assessments/{type}/questions` | 获取测评题目 |
| POST | `/api/v1/assessments/{id}/answer` | 提交单题答案 |
| POST | `/api/v1/assessments/{id}/submit` | 提交整个测评 |
| GET | `/api/v1/assessments/{id}/result` | 获取测评结果 |
| GET | `/api/v1/assessments/history` | 获取历史测评列表 |
| GET | `/api/v1/assessments/{type}/history` | 获取某类测评历史趋势 |

### 4.5 模块3：成长画像 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/portrait` | 获取画像总览仪表盘数据 |
| GET | `/api/v1/portrait/academic` | 获取专业知识维度详情 |
| GET | `/api/v1/portrait/ability` | 获取通用能力维度详情 |
| GET | `/api/v1/portrait/practice` | 获取实践能力维度详情 |
| GET | `/api/v1/portrait/career` | 获取职业准备度详情 |
| GET | `/api/v1/portrait/interest-goal` | 获取兴趣与目标分析 |
| GET | `/api/v1/portrait/goal-execution` | 获取目标清晰度与执行力 |
| GET | `/api/v1/portrait/history` | 获取历史画像趋势数据 |
| POST | `/api/v1/portrait/export/pdf` | 导出 PDF 报告 |
| GET | `/api/v1/portrait/share` | 生成画像快照分享链接 |

### 4.6 模块4：方向分析 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/directions` | 获取所有方向分析概览 |
| POST | `/api/v1/directions/analyze` | AI 触发全方向分析 |
| GET | `/api/v1/directions/employment` | 获取就业方向分析结果 |
| GET | `/api/v1/directions/graduate` | 获取考研方向分析结果 |
| GET | `/api/v1/directions/entrepreneurship` | 获取创业方向分析结果 |
| GET | `/api/v1/directions/comparison` | 获取多方向对比数据 |
| GET | `/api/v1/directions/{id}/matching-detail` | 获取匹配度详细分解 |

### 4.7 模块5：规划生成 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/plans` | 获取规划列表 |
| POST | `/api/v1/plans/generate` | AI 自动生成规划 |
| GET | `/api/v1/plans/{id}` | 获取规划详情 |
| PUT | `/api/v1/plans/{id}` | 手动更新规划 |
| GET | `/api/v1/plans/{id}/milestones` | 获取里程碑列表 |
| PUT | `/api/v1/plans/milestones/{id}` | 更新里程碑状态 |
| POST | `/api/v1/plans/{id}/adjust` | AI 建议 + 手动调整规划 |
| GET | `/api/v1/plans/{id}/adjustments` | 获取调整日志 |

### 4.8 模块6：任务管理 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/tasks` | 获取任务列表（支持筛选/搜索） |
| POST | `/api/v1/tasks` | 创建任务 |
| GET | `/api/v1/tasks/{id}` | 获取任务详情 |
| PUT | `/api/v1/tasks/{id}` | 更新任务 |
| DELETE | `/api/v1/tasks/{id}` | 删除任务 |
| PUT | `/api/v1/tasks/{id}/status` | 更新任务状态 |
| PUT | `/api/v1/tasks/{id}/progress` | 更新进度百分比 |
| POST | `/api/v1/tasks/{id}/deliverables` | 上传成果文件 |
| POST | `/api/v1/tasks/{id}/subtasks` | AI 拆解子任务 |
| GET | `/api/v1/tasks/board` | 获取看板数据 |
| GET | `/api/v1/tasks/calendar` | 获取日历视图数据 |
| GET | `/api/v1/tasks/reviews` | 获取复盘报告列表 |
| POST | `/api/v1/tasks/reviews/generate` | AI 生成复盘报告 |
| POST | `/api/v1/tasks/{id}/evaluate` | AI/教师评价任务 |
| GET | `/api/v1/tasks/templates` | 获取任务模板库 |

### 4.9 模块7：智能问答 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/qa/sessions` | 获取会话列表 |
| POST | `/api/v1/qa/sessions` | 创建新会话 |
| GET | `/api/v1/qa/sessions/{id}` | 获取会话消息历史 |
| DELETE | `/api/v1/qa/sessions/{id}` | 删除会话 |
| POST | `/api/v1/qa/sessions/{id}/messages` | 发送消息（AI 回复） |
| PUT | `/api/v1/qa/sessions/{id}/favorite` | 收藏/取消收藏会话 |
| POST | `/api/v1/qa/upload-context` | 上传教材/讲义作为上下文 |

### 4.10 模块8：内容生成 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/contents` | 获取已生成内容列表 |
| POST | `/api/v1/contents/report` | AI 生成成长报告 |
| POST | `/api/v1/contents/resume` | AI 生成简历 |
| POST | `/api/v1/contents/statement` | AI 生成个人陈述 |
| POST | `/api/v1/contents/story` | AI 生成成长故事 |
| POST | `/api/v1/contents/script` | AI 生成视频脚本 |
| POST | `/api/v1/contents/poster` | AI 生成海报文案 |
| POST | `/api/v1/contents/summary` | AI 生成年度总结 |
| GET | `/api/v1/contents/{id}` | 获取生成内容详情 |
| PUT | `/api/v1/contents/{id}` | 手动编辑内容 |
| POST | `/api/v1/contents/{id}/export` | 导出（PDF/Word） |

### 4.11 文件上传通用 API

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/upload` | 上传文件（multipart） |
| DELETE | `/api/v1/upload/{id}` | 删除文件 |

---

## 五、前端路由与页面详细清单

### 5.1 路由结构

```
/                              # 首页/引导页（未登录跳转登录）
/auth/login                    # 登录
/auth/register                 # 注册

/dashboard                     # 仪表盘（各模块入口汇总）

# 模块1：个人成长档案
/profile                       # 档案主页（九宫格导航）
/profile/basic-info            # 基本信息（表单）
/profile/academics             # 学业信息（课程列表+GPA）
/profile/interests             # 兴趣标签（标签管理）
/profile/projects              # 项目/竞赛/科研（卡片列表+新增表单）
/profile/internships           # 实习/实践（时间线+表单）
/profile/certificates          # 证书/技能（列表+表单）
/profile/portfolio             # 作品集（网格展示+上传）
/profile/goals                 # 目标意向（排序+管理）
/profile/authorization         # 信息授权（授权码管理）

# 模块2：智能测评
/assessment                    # 测评中心（各测评入口卡片）
/assessment/holland            # 霍兰德兴趣测评（答题流程）
/assessment/ability            # 能力自评（答题流程）
/assessment/values             # 职业价值观测评（排序题）
/assessment/learning-habit     # 学习习惯测评
/assessment/readiness          # 准备度测评
/assessment/result/:id         # 测评结果页（雷达图+分析）

# 模块3：成长画像
/portrait                      # 画像总览仪表盘（雷达图+得分）
/portrait/academic             # 专业知识维度
/portrait/ability              # 通用能力维度
/portrait/practice             # 实践能力维度
/portrait/career               # 职业准备度
/portrait/export               # 导出与分享

# 模块4：方向分析
/direction                     # 方向分析主页（三方向卡片）
/direction/employment          # 就业方向分析详情
/direction/graduate            # 考研方向分析详情
/direction/entrepreneurship    # 创业方向分析详情
/direction/comparison          # 多方向对比看板

# 模块5：规划生成
/plan                          # 规划总览（时间轴+甘特图）
/plan/overall                  # 大学四年总体规划
/plan/term                     # 学期/月度规划
/plan/milestone                # 关键里程碑管理
/plan/adjustment               # 动态调整

# 模块6：任务管理
/tasks                         # 任务看板（默认看板视图）
/tasks?view=list               # 列表视图
/tasks?view=calendar           # 日历视图
/tasks/create                  # 创建任务
/tasks/:id                     # 任务详情
/tasks/review                  # 任务复盘

# 模块7：智能问答
/qa                            # 问答主页（会话列表+聊天窗）
/qa/session/:id                # 具体会话

# 模块8：内容生成
/content                       # 内容生成中心
/content/report                # 成长报告生成
/content/resume                # 简历生成
/content/statement             # 个人陈述生成
/content/story                 # 成长故事生成
/content/script                # 视频脚本生成
/content/poster                # 海报文案生成
/content/summary               # 年度总结生成
```

### 5.2 前端核心共享组件清单

| 组件 | 路径 | 功能说明 |
|------|------|----------|
| `AppShell` | `components/layout/AppShell.tsx` | 全局布局：侧边栏 + 顶部栏 + 内容区 |
| `Sidebar` | `components/layout/Sidebar.tsx` | 侧边导航菜单（模块切换） |
| `Navbar` | `components/layout/Navbar.tsx` | 顶部栏（搜索、通知、用户头像） |
| `FileUpload` | `components/common/FileUpload.tsx` | 通用文件上传（拖拽+点击，支持预览） |
| `RichTextEditor` | `components/common/RichTextEditor.tsx` | 富文本编辑器（基于 TipTap） |
| `TagInput` | `components/common/TagInput.tsx` | 标签输入组件 |
| `ProgressSteps` | `components/common/ProgressSteps.tsx` | 步骤进度条（测评流程用） |
| `RadarChart` | `components/charts/RadarChart.tsx` | 雷达图（能力/兴趣可视化） |
| `LineChart` | `components/charts/LineChart.tsx` | 折线图（趋势展示） |
| `BarChart` | `components/charts/BarChart.tsx` | 柱状图（对比展示） |
| `GanttChart` | `components/charts/GanttChart.tsx` | 甘特图（规划时间轴） |

---

## 六、后端核心代码架构

### 6.1 应用入口

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import (
    auth, users, upload,
    profile, assessment, portrait,
    direction, plan, tasks, qa, content
)
from app.database import engine, Base

app = FastAPI(title="College Growth Platform API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["文件上传"])

app.include_router(profile.basic_info.router, prefix="/api/v1/profile", tags=["个人档案-基本信息"])
app.include_router(profile.academics.router, prefix="/api/v1/profile", tags=["个人档案-学业信息"])
app.include_router(profile.interests.router, prefix="/api/v1/profile", tags=["个人档案-兴趣标签"])
app.include_router(profile.projects.router, prefix="/api/v1/profile", tags=["个人档案-项目经验"])
app.include_router(profile.internships.router, prefix="/api/v1/profile", tags=["个人档案-实习实践"])
app.include_router(profile.certificates.router, prefix="/api/v1/profile", tags=["个人档案-证书技能"])
app.include_router(profile.portfolio.router, prefix="/api/v1/profile", tags=["个人档案-作品集"])
app.include_router(profile.goals.router, prefix="/api/v1/profile", tags=["个人档案-目标意向"])
app.include_router(profile.authorization.router, prefix="/api/v1/profile", tags=["个人档案-信息授权"])

app.include_router(assessment.holland.router, prefix="/api/v1/assessments", tags=["智能测评-兴趣"])
app.include_router(assessment.ability.router, prefix="/api/v1/assessments", tags=["智能测评-能力"])
app.include_router(assessment.values.router, prefix="/api/v1/assessments", tags=["智能测评-价值观"])
app.include_router(assessment.learning_habit.router, prefix="/api/v1/assessments", tags=["智能测评-学习习惯"])
app.include_router(assessment.readiness.router, prefix="/api/v1/assessments", tags=["智能测评-准备度"])

app.include_router(portrait.overview.router, prefix="/api/v1/portrait", tags=["成长画像-总览"])
app.include_router(portrait.academics.router, prefix="/api/v1/portrait", tags=["成长画像-学业"])
app.include_router(portrait.ability.router, prefix="/api/v1/portrait", tags=["成长画像-能力"])
app.include_router(portrait.practice.router, prefix="/api/v1/portrait", tags=["成长画像-实践"])
app.include_router(portrait.career.router, prefix="/api/v1/portrait", tags=["成长画像-职业"])
app.include_router(portrait.export.router, prefix="/api/v1/portrait", tags=["成长画像-导出"])

app.include_router(direction.employment.router, prefix="/api/v1/directions", tags=["方向分析-就业"])
app.include_router(direction.graduate.router, prefix="/api/v1/directions", tags=["方向分析-考研"])
app.include_router(direction.entrepreneurship.router, prefix="/api/v1/directions", tags=["方向分析-创业"])
app.include_router(direction.comparison.router, prefix="/api/v1/directions", tags=["方向分析-对比"])

app.include_router(plan.overall.router, prefix="/api/v1/plans", tags=["规划生成-总规划"])
app.include_router(plan.term_plan.router, prefix="/api/v1/plans", tags=["规划生成-学期计划"])
app.include_router(plan.milestone.router, prefix="/api/v1/plans", tags=["规划生成-里程碑"])
app.include_router(plan.alternative.router, prefix="/api/v1/plans", tags=["规划生成-备选方案"])
app.include_router(plan.adjustment.router, prefix="/api/v1/plans", tags=["规划生成-动态调整"])

app.include_router(tasks.tasks.router, prefix="/api/v1/tasks", tags=["任务管理-任务"])
app.include_router(tasks.board.router, prefix="/api/v1/tasks", tags=["任务管理-看板"])
app.include_router(tasks.review.router, prefix="/api/v1/tasks", tags=["任务管理-复盘"])
app.include_router(tasks.evaluation.router, prefix="/api/v1/tasks", tags=["任务管理-评价"])

app.include_router(qa.chat.router, prefix="/api/v1/qa", tags=["智能问答-聊天"])
app.include_router(qa.session.router, prefix="/api/v1/qa", tags=["智能问答-会话"])
app.include_router(qa.knowledge.router, prefix="/api/v1/qa", tags=["智能问答-知识库"])

app.include_router(content.report.router, prefix="/api/v1/contents", tags=["内容生成-报告"])
app.include_router(content.resume.router, prefix="/api/v1/contents", tags=["内容生成-简历"])
app.include_router(content.statement.router, prefix="/api/v1/contents", tags=["内容生成-陈述"])
app.include_router(content.story.router, prefix="/api/v1/contents", tags=["内容生成-故事"])
app.include_router(content.script.router, prefix="/api/v1/contents", tags=["内容生成-脚本"])
app.include_router(content.poster.router, prefix="/api/v1/contents", tags=["内容生成-海报"])
app.include_router(content.summary.router, prefix="/api/v1/contents", tags=["内容生成-总结"])

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "College Growth Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 6.2 配置文件

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "College Growth Platform API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/college_growth"
    DB_ECHO: bool = False

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时

    # AI API
    AI_API_KEY: str = ""
    AI_API_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o"

    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".jpg", ".png", ".pdf", ".doc", ".docx", ".zip"]

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### 6.3 数据库连接

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 6.4 AI 服务统一封装

```python
# backend/app/services/ai_service.py
import httpx
from typing import Optional
from app.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_API_BASE_URL
        self.model = settings.AI_MODEL

    async def chat(self, messages: list, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": full_messages,
                    "temperature": temperature
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def analyze_portrait(self, user_data: dict) -> dict:
        """分析成长画像"""
        system_prompt = "你是一名大学生成长发展分析专家。请根据用户数据生成多维度成长画像分析。"
        messages = [{"role": "user", "content": f"请分析以下用户数据：{user_data}"}]
        result = await self.chat(messages, system_prompt)
        return {"analysis": result}

    async def recommend_directions(self, portrait_data: dict) -> dict:
        """推荐发展方向"""
        system_prompt = "你是一名职业规划专家。请根据学生成长画像推荐就业/考研/创业方向。"
        messages = [{"role": "user", "content": f"请分析画像数据并推荐方向：{portrait_data}"}]
        result = await self.chat(messages, system_prompt)
        return {"recommendation": result}

    async def generate_plan(self, user_profile: dict, direction_result: dict) -> dict:
        """生成成长规划"""
        system_prompt = "你是一名教育规划专家。请为目标方向生成详细的大学成长规划。"
        messages = [{"role": "user", "content": f"用户信息：{user_profile}\n目标方向：{direction_result}"}]
        result = await self.chat(messages, system_prompt)
        return {"plan": result}

    async def answer_question(self, question: str, context: Optional[str] = None) -> str:
        """智能问答"""
        system_prompt = "你是一名大学生全场景智能助手，能回答学习、就业、考研、留学、创业等各类问题。"
        full_context = f"上下文：{context}\n问题：{question}" if context else question
        messages = [{"role": "user", "content": full_context}]
        return await self.chat(messages, system_prompt)

    async def generate_content(self, content_type: str, params: dict) -> str:
        """生成各类内容"""
        prompts = {
            "report": "请根据学生数据生成学期成长报告",
            "resume": "请根据学生档案信息生成专业简历",
            "statement": "请根据目标院校/岗位生成个人陈述",
            "story": "请根据学生经历生成个人成长故事",
            "script": "请根据主题生成视频脚本",
            "poster": "请根据活动信息生成海报文案",
            "summary": "请根据年度数据生成年度成长总结"
        }
        system_prompt = f"你是一名专业的内容创作专家。{prompts.get(content_type, '')}"
        messages = [{"role": "user", "content": f"参数：{params}"}]
        return await self.chat(messages, system_prompt)

ai_service = AIService()
```

### 6.5 认证依赖

```python
# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

---

## 七、前端核心代码架构

### 7.1 API 请求封装

```typescript
// frontend/src/lib/api.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截器 - 添加 JWT
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error.response?.data || error);
  }
);

// 通用 API 方法
export const apiService = {
  get: <T>(url: string, config?: AxiosRequestConfig) => api.get<any, T>(url, config),
  post: <T>(url: string, data?: any, config?: AxiosRequestConfig) => api.post<any, T>(url, data, config),
  put: <T>(url: string, data?: any, config?: AxiosRequestConfig) => api.put<any, T>(url, data, config),
  delete: <T>(url: string, config?: AxiosRequestConfig) => api.delete<any, T>(url, config),
  upload: <T>(url: string, formData: FormData) =>
    api.post<any, T>(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
};

export default api;
```

### 7.2 Zustand 状态管理示例

```typescript
// frontend/src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  role: 'student' | 'teacher' | 'admin';
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (user, token) =>
        set({ user, token, isAuthenticated: true }),
      logout: () =>
        set({ user: null, token: null, isAuthenticated: false }),
      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    { name: 'auth-storage' }
  )
);
```

```typescript
// frontend/src/store/profileStore.ts
import { create } from 'zustand';

interface ProfileState {
  profile: any | null;
  isLoading: boolean;
  error: string | null;
  fetchProfile: () => Promise<void>;
  updateBasicInfo: (data: any) => Promise<void>;
  // ... 更多 actions
}

export const useProfileStore = create<ProfileState>((set) => ({
  profile: null,
  isLoading: false,
  error: null,
  fetchProfile: async () => {
    set({ isLoading: true });
    try {
      const res = await api.get('/profile');
      set({ profile: res.data, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },
  updateBasicInfo: async (data) => {
    set({ isLoading: true });
    try {
      const res = await api.put('/profile/basic-info', data);
      set({ profile: { ...res.data }, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },
}));
```

### 7.3 自定义 Hooks 模式

```typescript
// frontend/src/hooks/useAuth.ts
'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { apiService } from '@/lib/api';

export function useAuth(requireAuth: boolean = true) {
  const router = useRouter();
  const { user, token, isAuthenticated, setAuth, logout } = useAuthStore();

  useEffect(() => {
    if (requireAuth && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [requireAuth, isAuthenticated, router]);

  const login = async (email: string, password: string) => {
    const res: any = await apiService.post('/auth/login', { email, password });
    setAuth(res.data.user, res.data.access_token);
    return res.data;
  };

  const register = async (email: string, password: string, nickname: string) => {
    const res: any = await apiService.post('/auth/register', { email, password, nickname });
    setAuth(res.data.user, res.data.access_token);
    return res.data;
  };

  return { user, token, isAuthenticated, login, register, logout };
}
```

### 7.4 TypeScript 类型定义

```typescript
// frontend/src/types/user.ts
export interface User {
  id: string;
  email: string;
  phone?: string;
  nickname: string;
  avatar_url?: string;
  role: 'student' | 'teacher' | 'admin';
  created_at: string;
}

// frontend/src/types/profile.ts
export interface Profile {
  id: string;
  real_name?: string;
  gender?: 'male' | 'female' | 'other';
  birth_date?: string;
  bio?: string;
  academics?: AcademicInfo;
  interests?: InterestTag[];
  projects?: ProjectExperience[];
  internships?: Internship[];
  certificates?: Certificate[];
  skills?: Skill[];
  portfolio_items?: PortfolioItem[];
  goals?: GoalIntention[];
}

export interface AcademicInfo {
  school: string;
  college?: string;
  major: string;
  grade?: string;
  student_id?: string;
  enrollment_year: number;
  gpa?: number;
  courses?: Course[];
}

export interface Course {
  id: string;
  name: string;
  score?: number;
  credit: number;
  semester?: string;
  course_type: 'required' | 'elective' | 'public';
}

export interface InterestTag {
  id: string;
  name: string;
  weight: number;
  source: 'manual' | 'assessment';
}

export interface ProjectExperience {
  id: string;
  title: string;
  role: 'leader' | 'core_member' | 'participant';
  start_date: string;
  end_date?: string;
  description?: string;
  award_level?: 'school' | 'provincial' | 'national' | 'international';
  project_type: 'competition' | 'research' | 'project';
}

export interface Internship {
  id: string;
  company: string;
  position: string;
  start_date: string;
  end_date?: string;
  description?: string;
}

export interface Certificate {
  id: string;
  name: string;
  issuer?: string;
  obtain_date?: string;
}

export interface Skill {
  id: string;
  name: string;
  proficiency: 'beginner' | 'learning' | 'mastering' | 'expert';
  category: 'hard' | 'soft';
}

export interface PortfolioItem {
  id: string;
  title: string;
  category: 'code' | 'design' | 'writing' | 'video' | 'other';
  description?: string;
  is_public: boolean;
}

export interface GoalIntention {
  id: string;
  intention_type: 'employment' | 'graduate' | 'study_abroad' | 'entrepreneurship' | 'civil_service';
  target_content?: any;
  priority: number;
}

// frontend/src/types/assessment.ts
export interface Assessment {
  id: string;
  type: 'holland' | 'ability' | 'values' | 'learning_habit' | 'readiness';
  status: 'not_started' | 'in_progress' | 'completed';
  current_question: number;
  total_questions: number;
  result?: AssessmentResult;
}

export interface AssessmentQuestion {
  id: string;
  dimension?: string;
  question_text: string;
  options: { label: string; value: number }[];
}

export interface AssessmentResult {
  id: string;
  type: string;
  result_data: any;
  summary?: string;
}

// frontend/src/types/portrait.ts
export interface Portrait {
  overall_score?: number;
  academic_score?: number;
  ability_score?: { [key: string]: number };
  practice_score?: { [key: string]: any };
  career_readiness?: { [key: string]: any };
  interest_match?: { [key: string]: any };
  goal_clarity?: { [key: string]: any };
}

// frontend/src/types/task.ts
export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'completed' | 'delayed';
  priority: 'p0' | 'p1' | 'p2';
  progress: number;
  tag: 'academic' | 'practice' | 'ability' | 'other';
  due_date?: string;
  subtasks?: Task[];
  deliverables?: TaskDeliverable[];
}

export interface TaskDeliverable {
  id: string;
  file_url?: string;
  description?: string;
}

// frontend/src/types/qa.ts
export interface QASession {
  id: string;
  title?: string;
  category?: string;
  is_favorite: boolean;
  message_count: number;
  messages?: QAMessage[];
}

export interface QAMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  knowledge_sources?: { title: string; url: string }[];
}

// frontend/src/types/plan.ts
export interface GrowthPlan {
  id: string;
  plan_type: 'overall' | 'yearly' | 'semester' | 'monthly' | 'weekly';
  period_start: string;
  period_end: string;
  content: any;
  status: 'active' | 'completed' | 'archived';
  milestones?: Milestone[];
}

export interface Milestone {
  id: string;
  name: string;
  due_date: string;
  status: 'pending' | 'in_progress' | 'completed' | 'delayed';
  is_key_milestone: boolean;
}

// frontend/src/types/content.ts
export interface GeneratedContent {
  id: string;
  type: string;
  title?: string;
  content: string;
  status: 'draft' | 'finalized';
  version: number;
}

// frontend/src/types/direction.ts
export interface DirectionAnalysis {
  id: string;
  type: 'employment' | 'graduate' | 'entrepreneurship';
  result_data: any;
  match_score?: number;
  confidence?: 'high' | 'medium' | 'low';
}
```

---

## 八、开发阶段与执行顺序

### 阶段一：项目初始化（Day 1）

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1.1 | 创建项目根目录 `college-growth-platform/` | 初始化 Git 仓库 |
| 1.2 | 初始化后端项目：`backend/` | 创建 FastAPI 项目骨架 |
| 1.3 | 初始化前端项目：`frontend/` | `npx create-next-app@latest frontend` |
| 1.4 | 搭建 Docker 环境 | 编写 `docker-compose.yml` |
| 1.5 | 配置数据库 | 编写 Alembic 初始迁移 |

### 阶段二：P0 核心模块（Day 2-5）

| 模块 | 后端任务 | 前端任务 | 预估工时 |
|------|---------|---------|----------|
| **用户认证** | User 模型 + JWT 认证 API | 登录/注册页面 + store | 0.5天 |
| **个人成长档案** | 9 个子模块 CRUD API | 9 个页面 + 表单组件 | 2天 |
| **智能测评** | 测评引擎 + 题目管理 API | 答题流程 + 结果可视化 | 1.5天 |
| **成长画像** | 画像计算 + 聚合 API | 仪表盘 + 图表组件 | 1天 |

### 阶段三：P1 重要模块（Day 6-8）

| 模块 | 后端任务 | 前端任务 | 预估工时 |
|------|---------|---------|----------|
| **方向分析** | AI 分析 + 推荐 API | 方向展示 + 对比页面 | 1.5天 |
| **规划生成** | AI 规划生成 API | 甘特图 + 时间轴页面 | 1.5天 |

### 阶段四：P2 增强模块（Day 9-11）

| 模块 | 后端任务 | 前端任务 | 预估工时 |
|------|---------|---------|----------|
| **任务管理** | 任务 CRUD + 看板 API | 看板 + 日历 + 复盘页面 | 1.5天 |
| **智能问答** | 对话 API + AI 集成 | 聊天界面 + 会话管理 | 1.5天 |

### 阶段五：P3 + 集成测试（Day 12-14）

| 步骤 | 操作 | 说明 |
|------|------|------|
| 5.1 | 内容生成模块 | AI 内容生成 API + 页面 |
| 5.2 | 文件上传集成 | 统一上传组件 + 后端处理 |
| 5.3 | 全链路联调 | 数据流闭环测试 |
| 5.4 | Docker 部署 | 编写 Dockerfile + Nginx 配置 |
| 5.5 | 文档整理 | API 文档 + 部署说明 |

---

## 九、配置文件清单

### 9.1 docker-compose.yml

```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: college_user
      POSTGRES_PASSWORD: college_pass
      POSTGRES_DB: college_growth
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://college_user:college_pass@db:5432/college_growth
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      AI_API_KEY: ${AI_API_KEY}
    depends_on:
      - db
    volumes:
      - ./backend/uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

### 9.2 backend/requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0
openpyxl==3.1.2
python-dotenv==1.0.0
```

### 9.3 frontend/package.json (关键依赖)

```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.5",
    "recharts": "^2.10.0",
    "lucide-react": "^0.312.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "react-hook-form": "^7.49.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.4",
    "@tiptap/react": "^2.1.0",
    "@tiptap/starter-kit": "^2.1.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-tabs": "^1.0.4"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

### 9.4 .env 配置模板

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://college_user:college_pass@localhost:5432/college_growth
JWT_SECRET_KEY=your-random-secret-key-change-in-production
AI_API_KEY=sk-your-openai-api-key
AI_API_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o
UPLOAD_DIR=./uploads
```

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 十、Trae 开发使用指南

### 10.1 项目生成顺序建议

Trae 可以按照以下顺序逐模块生成代码：

```
Round 1: 项目骨架搭建
  ├── docker-compose.yml + 配置文件
  ├── backend: main.py + config.py + database.py
  └── frontend: Next.js 初始化 + 布局组件

Round 2: 用户认证 (P0)
  ├── backend: User 模型 + auth API
  └── frontend: 登录/注册页面

Round 3: 个人成长档案 (P0)
  ├── backend: 9 个子模块模型 + CRUD API
  └── frontend: 9 个管理页面 + 表单组件

Round 4: 智能测评 (P0)
  ├── backend: 测评模型 + 答题引擎 API
  └── frontend: 测评流程 + 结果页面

Round 5: 成长画像 (P0)
  ├── backend: 画像聚合计算 API
  └── frontend: 仪表盘 + 图表

Round 6: 方向分析 (P1)
  ├── backend: AI 方向分析 API
  └── frontend: 方向展示 + 对比

Round 7: 规划生成 (P1)
  ├── backend: AI 规划生成 API
  └── frontend: 甘特图 + 时间轴

Round 8: 任务管理 (P2)
  ├── backend: 任务 CRUD + 看板 API
  └── frontend: 看板 + 日历 + 复盘

Round 9: 智能问答 (P2)
  ├── backend: 对话 API + AI 集成
  └── frontend: 聊天界面

Round 10: 内容生成 (P3)
  ├── backend: 内容生成 API
  └── frontend: 内容中心页面
```

### 10.2 给 Trae 的指令模板

在每个 Round 开始时，向 Trae 发送以下格式的指令：

```
请基于文档 [项目文档路径] 生成 [模块名] 的完整代码。

需要完成：
1. 后端：
   - 数据模型：参考文档第三章的 [模型名]
   - API 路由：参考文档第四章的 [API 列表]
   - 业务逻辑：在 services/ 中实现核心逻辑
   - AI 集成：通过 ai_service.py 调用 AI

2. 前端：
   - 页面：参考文档第五章的 [路由路径]
   - 组件：使用共享组件库中的组件
   - API 调用：通过 lib/api.ts 封装的请求方法
   - 状态管理：按需使用 Zustand store

3. 类型定义：
   - 后端：在 schemas/ 中定义 Pydantic 模型
   - 前端：在 types/ 中定义 TypeScript 接口

注意事项：
- 遵循现有的代码风格和架构约定
- 确保 API 路径与前端调用一致
- 添加适当的错误处理和输入验证
```

---

## 十一、数据流闭环验证

### 11.1 核心数据流测试场景

```
场景：学生完成从信息录入到任务复盘的完整闭环

1. 学生登录 → 填写基本信息 + 学业信息
2. 完成 Holland 兴趣测评 → 系统生成兴趣代码（如 RIA）
3. 完成能力自评 → 系统计算各维度能力分数
4. 查看成长画像仪表盘 → 看到雷达图 + 各维度评分
5. 触发方向分析 → AI 推荐就业/考研/创业方向
6. 选择方向 → AI 生成四年总体规划
7. 规划自动拆分为任务 → 任务出现在看板中
8. 完成任务 → 上传成果 → AI 评价
9. 周复盘 → AI 生成复盘报告 → 数据更新到画像
10. 画像数据更新 → 方向分析重新校准
```

### 11.2 数据一致性保障

| 触发点 | 更新操作 | 影响模块 |
|--------|---------|---------|
| 测评完成 | 更新 AssessmentHistory + 重算 Portrait | 测评 → 画像 |
| 画像更新 | 重新计算各维度得分 | 画像 → 方向分析 |
| 方向分析完成 | 存储 DirectionAnalysis | 方向分析 → 规划生成 |
| 规划生成 | 自动创建 Task | 规划生成 → 任务管理 |
| 任务完成 | 更新进度 + 写 Evaluation | 任务管理 → 画像 |
| 档案更新 | 标记画像需要重算 | 档案 → 画像 |

---

## 十二、模块功能细化（保留原文档内容）

（保留原始 MVP 开发任务规划文档中"二、模块功能细化"的完整内容，此处从略。）

---

## 附：关键决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 用户 ID 类型 | UUID | 分布式友好，安全不递增 |
| 文件存储 | 本地磁盘 + S3 兼容 | MVP 阶段先本地，后期迁移 |
| 测评引擎 | 服务端计算 | 保证结果一致性，支持 AI 分析 |
| 规划生成 | AI + 人工编辑 | AI 初稿 + 用户微调保证质量 |
| AI 调用 | 统一 AIService 封装 | 便于切换模型/供应商 |
| 状态管理 | Zustand + React Query | Zustand 管理客户端状态，React Query 管理服务端缓存 |
| 权限控制 | JWT + 字段级授权 | 满足信息授权管理需求 |