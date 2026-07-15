"""
学习资源提供者 (ResourceProvider)。

Provider 模式: 当前使用 HardCodedResourceProvider (MVP)，
未来可替换为 WebResourceProvider 或 RAGResourceProvider。

Orchestrator 只依赖 ResourceProvider 接口，不关心具体实现。
"""

from typing import Protocol

from src.models import Resource


# ── Provider 接口 ─────────────────────────────────────────

class ResourceProvider(Protocol):
    """资源提供者协议。

    所有 Provider 实现必须遵循此接口。
    """

    def get_resources(self, topic: str, difficulty: str) -> list[Resource]:
        """获取指定主题和难度等级的学习资源。

        Args:
            topic: 主题名称
            difficulty: 难度等级 (beginner/intermediate/advanced)

        Returns:
            list[Resource]: 匹配的学习资源列表
        """
        ...


# ── MVP 实现: 硬编码资源映射 ──────────────────────────────

class HardCodedResourceProvider:
    """MVP 资源提供者 — 基于关键词匹配的内置映射表。

    后续可替换为:
    - WebResourceProvider: 调用在线 API 搜索资源
    - RAGResourceProvider: 向量检索知识库
    """

    def __init__(self) -> None:
        self._mapping: dict[str, list[dict]] = self._build_mapping()

    def get_resources(self, topic: str, difficulty: str) -> list[dict]:
        """按 topic 关键词匹配返回资源。

        匹配规则: topic 中包含 mapping 的 key 时返回对应资源。
        """
        results: list[dict] = []
        for keyword, resources in self._mapping.items():
            if keyword.lower() in topic.lower():
                for r in resources:
                    results.append(Resource(
                        title=r["title"],
                        type=r["type"],  # type: ignore[arg-type]
                        url=r.get("url"),
                        topic=topic,
                        estimated_hours=r.get("estimated_hours"),
                        free=r.get("free", True),
                        difficulty=difficulty,  # type: ignore[arg-type]
                    ).model_dump())
        return results

    # ── 内置资源库 ───────────────────────────────────

    @staticmethod
    def _build_mapping() -> dict[str, list[dict]]:
        """构建关键词 → 资源列表的映射表。

        每个关键词对应 1-2 条高质量免费资源。
        """
        return {
            "变量": [
                {"title": "Python 官方教程 — 数据类型", "type": "documentation",
                 "url": "https://docs.python.org/3/tutorial/introduction.html",
                 "estimated_hours": 2.0, "free": True},
            ],
            "数据类型": [
                {"title": "Python 官方教程 — 数据类型", "type": "documentation",
                 "url": "https://docs.python.org/3/tutorial/introduction.html",
                 "estimated_hours": 2.0, "free": True},
            ],
            "流程控制": [
                {"title": "Python 官方教程 — 控制流", "type": "documentation",
                 "url": "https://docs.python.org/3/tutorial/controlflow.html",
                 "estimated_hours": 2.0, "free": True},
            ],
            "循环": [
                {"title": "Real Python — 循环与迭代", "type": "tutorial",
                 "url": "https://realpython.com/python-for-loop/",
                 "estimated_hours": 1.5, "free": True},
            ],
            "函数": [
                {"title": "Python 官方教程 — 函数", "type": "documentation",
                 "url": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions",
                 "estimated_hours": 1.5, "free": True},
            ],
            "面向对象": [
                {"title": "Real Python — OOP 教程", "type": "tutorial",
                 "url": "https://realpython.com/python3-object-oriented-programming/",
                 "estimated_hours": 2.0, "free": True},
            ],
            "OOP": [
                {"title": "Real Python — OOP 教程", "type": "tutorial",
                 "url": "https://realpython.com/python3-object-oriented-programming/",
                 "estimated_hours": 2.0, "free": True},
            ],
            "文件": [
                {"title": "Python 官方教程 — 文件读写", "type": "documentation",
                 "url": "https://docs.python.org/3/tutorial/inputoutput.html",
                 "estimated_hours": 1.0, "free": True},
            ],
            "异常": [
                {"title": "Python 官方教程 — 错误与异常", "type": "documentation",
                 "url": "https://docs.python.org/3/tutorial/errors.html",
                 "estimated_hours": 1.0, "free": True},
            ],
            "标准库": [
                {"title": "Python 标准库速览", "type": "documentation",
                 "url": "https://docs.python.org/3/library/",
                 "estimated_hours": 3.0, "free": True},
            ],
            "虚拟环境": [
                {"title": "Python 虚拟环境指南", "type": "tutorial",
                 "url": "https://docs.python.org/3/tutorial/venv.html",
                 "estimated_hours": 0.5, "free": True},
            ],
            "数据库": [
                {"title": "SQL 教程 (W3Schools)", "type": "tutorial",
                 "url": "https://www.w3schools.com/sql/",
                 "estimated_hours": 8.0, "free": True},
            ],
            "SQL": [
                {"title": "SQL 教程 (W3Schools)", "type": "tutorial",
                 "url": "https://www.w3schools.com/sql/",
                 "estimated_hours": 8.0, "free": True},
            ],
            "Linux": [
                {"title": "Linux 命令行基础 (Ubuntu 官方)", "type": "tutorial",
                 "url": "https://ubuntu.com/tutorials/command-line-for-beginners",
                 "estimated_hours": 3.0, "free": True},
            ],
            "Shell": [
                {"title": "Bash 脚本入门", "type": "tutorial",
                 "url": "https://linuxconfig.org/bash-scripting-tutorial-for-beginners",
                 "estimated_hours": 4.0, "free": True},
            ],
            "Git": [
                {"title": "Pro Git Book (中文版)", "type": "book",
                 "url": "https://git-scm.com/book/zh/v2",
                 "estimated_hours": 10.0, "free": True},
            ],
            "Java": [
                {"title": "Java 官方教程 (Oracle)", "type": "documentation",
                 "url": "https://docs.oracle.com/javase/tutorial/",
                 "estimated_hours": 20.0, "free": True},
            ],
            "Hadoop": [
                {"title": "Hadoop 官方文档", "type": "documentation",
                 "url": "https://hadoop.apache.org/docs/stable/",
                 "estimated_hours": 15.0, "free": True},
            ],
            "Spark": [
                {"title": "Spark 官方编程指南", "type": "documentation",
                 "url": "https://spark.apache.org/docs/latest/",
                 "estimated_hours": 12.0, "free": True},
            ],
            "Kafka": [
                {"title": "Kafka 官方文档", "type": "documentation",
                 "url": "https://kafka.apache.org/documentation/",
                 "estimated_hours": 10.0, "free": True},
            ],
            "Flink": [
                {"title": "Flink 官方文档", "type": "documentation",
                 "url": "https://nightlies.apache.org/flink/flink-docs-stable/",
                 "estimated_hours": 12.0, "free": True},
            ],
            "通用": [
                {"title": "免费编程书籍合集 (GitHub)", "type": "book",
                 "url": "https://github.com/EbookFoundation/free-programming-books",
                 "estimated_hours": None, "free": True},
            ],
        }
