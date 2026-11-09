"""Проверяемые примеры: вход, цель и ожидаемый итоговый выбор."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    title: str
    facts: frozenset[str]
    goal: str
    expected: str | None
    goal_proved: bool


EXAMPLES = (
    Example("Выбор по приоритету", frozenset({"likes_science", "likes_adventure"}),
            "martian", "martian", True),
    Example("Два способа обосновать одну книгу", frozenset({"likes_science", "likes_philosophy"}),
            "solaris", "solaris", True),
    Example("Выбор более специфичного правила",
            frozenset({"likes_mystery", "prefers_short", "prefers_classics"}),
            "sherlock", "sherlock", True),
    Example("Фэнтези и приключения", frozenset({"likes_magic", "likes_adventure"}),
            "hobbit", "hobbit", True),
    Example("Равенство приоритета и специфичности",
            frozenset({"likes_science", "likes_magic", "likes_adventure"}),
            "hobbit", "martian", True),
    Example("Только общий интерес", frozenset({"likes_mystery"}),
            "orient_express", "orient_express", True),
    Example("Недостаточно фактов для рекомендации", frozenset({"likes_adventure"}),
            "martian", None, False),
    Example("Кандидат и недоказанная цель", frozenset({"likes_science"}),
            "martian", "solaris", False),
    Example("Нет положительных ответов", frozenset(),
            "solaris", None, False),
)
