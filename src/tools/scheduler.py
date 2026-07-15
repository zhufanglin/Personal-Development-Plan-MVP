"""
学习计划调度器 (Scheduler)。

职责: 将模块列表转换为按天分配的学习计划。
纯数学调度，不涉及课程/先修/可行性等业务逻辑。

规则:
- 贪心打包: 每天填充至 daily_hours 上限
- 跨天: 单模块超过 daily_hours 时跨天拆分，标记 continuation
- 复习日: 每 5 个学习日后插入 1 天
- 评估日: 最后一个模块完成后插入 1 天
"""

from src.models import DayEntry, DailyPlan

# ── 常量 ──────────────────────────────────────────────────

REVIEW_INTERVAL: int = 5  # 每 N 个学习日插入复习日


class Scheduler:
    """将模块列表调度为按天分配的学习计划。

    使用方式:
        scheduler = Scheduler()
        plan = scheduler.schedule(modules, daily_hours, duration_days)
    """

    def schedule(
        self,
        modules: list[dict],
        daily_hours: float,
        duration_days: int,
        start_date: str | None = None,
    ) -> dict:
        """主调度入口。

        Args:
            modules: Module 字典列表，按 order 排序
            daily_hours: 每日可用小时数
            duration_days: 用户计划天数（用于 warning 判断）
            start_date: 可选开始日期（ISO 格式，暂用于占位）

        Returns:
            DailyPlan.model_dump() 字典
        """
        # ── 贪心打包 ──────────────────────────────────
        study_days: list[DayEntry] = self._pack_modules(modules, daily_hours)

        # ── 插入复习日 ────────────────────────────────
        days_with_review: list[DayEntry] = self._insert_review_days(
            study_days, interval=REVIEW_INTERVAL
        )

        # ── 插入评估日 ────────────────────────────────
        final_days: list[DayEntry] = self._insert_assessment_day(days_with_review)

        # ── 计算汇总 ──────────────────────────────────
        has_review: bool = any(d.type == "review" for d in final_days)
        has_assessment: bool = any(d.type == "assessment" for d in final_days)
        total_hours: float = sum(d.hours for d in final_days)

        return DailyPlan(
            days=final_days,
            total_days=len(final_days),
            total_hours=total_hours,
            includes_review_days=has_review,
            includes_assessments=has_assessment,
        ).model_dump()

    # ── 内部方法 ──────────────────────────────────────

    def _pack_modules(
        self, modules: list[dict], daily_hours: float
    ) -> list[DayEntry]:
        """贪心打包: 将模块分配到每天。

        每个模块跟踪 remaining_hours，跨天时拆分并标记 continuation。
        """
        # 深拷贝并添加 remaining_hours 追踪
        queue: list[dict] = []
        for m in modules:
            queue.append({**m, "_remaining": m["hours"]})

        day_entries: list[DayEntry] = []
        current_day: int = 1

        while queue:
            remaining_today: float = daily_hours
            day_modules: list[dict] = []

            while remaining_today > 0 and queue:
                m = queue[0]
                alloc = min(remaining_today, m["_remaining"])
                day_modules.append({
                    "module_name": m["name"],
                    "hours_allocated": alloc,
                    "is_continuation": m["_remaining"] < m["hours"],
                })
                m["_remaining"] -= alloc
                remaining_today -= alloc

                if m["_remaining"] <= 0:
                    queue.pop(0)

            day_total: float = sum(dm["hours_allocated"] for dm in day_modules)
            topic_names: list[str] = [dm["module_name"] for dm in day_modules]

            day_entries.append(DayEntry(
                day=current_day,
                topics=topic_names,
                hours=day_total,
                type="study",
            ))
            current_day += 1

        return day_entries

    def _insert_review_days(
        self, days: list[DayEntry], interval: int
    ) -> list[DayEntry]:
        """每 interval 个学习日后插入一个复习日。"""
        result: list[DayEntry] = []
        study_count: int = 0

        for entry in days:
            result.append(entry)
            if entry.type == "study":
                study_count += 1
                if study_count % interval == 0:
                    # 在下一个 day number 插入复习日
                    review_day: int = entry.day + 1
                    # 后续 day number 需要 +1
                    self._shift_days(result, review_day)
                    result.append(DayEntry(
                        day=review_day,
                        topics=[],
                        hours=entry.hours,  # 复习日使用当日学时
                        type="review",
                    ))

        return result

    def _insert_assessment_day(self, days: list[DayEntry]) -> list[DayEntry]:
        """在最后一个模块后插入评估日。"""
        if not days:
            return days

        last = days[-1]
        assess_day: int = last.day + 1
        assess_hours: float = last.hours if last.hours > 0 else 2.0

        days.append(DayEntry(
            day=assess_day,
            topics=[],
            hours=assess_hours,
            type="assessment",
        ))
        return days

    @staticmethod
    def _shift_days(days: list[DayEntry], from_day: int) -> None:
        """将指定 day number 之后的条目 day+1。"""
        for entry in days:
            if entry.day >= from_day:
                entry.day += 1
