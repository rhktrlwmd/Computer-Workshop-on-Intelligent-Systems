"""Учебная база знаний для варианта 3: подбор книги."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    conditions: tuple[str, ...]
    conclusion: str
    priority: int


INPUTS = {
    "likes_science": "Интересуется наукой",
    "likes_mystery": "Любит расследования и загадки",
    "likes_magic": "Любит истории о магии",
    "likes_adventure": "Любит приключения",
    "likes_philosophy": "Любит философские вопросы",
    "prefers_short": "Предпочитает короткие произведения",
    "prefers_classics": "Предпочитает классику",
}

BOOKS = {
    "solaris": "Станислав Лем «Солярис»",
    "martian": "Энди Вейер «Марсианин»",
    "orient_express": "Агата Кристи «Убийство в Восточном экспрессе»",
    "sherlock": "Артур Конан Дойл «Приключения Шерлока Холмса»",
    "earthsea": "Урсула Ле Гуин «Волшебник Земноморья»",
    "hobbit": "Джон Р. Р. Толкин «Хоббит»",
}

LABELS = INPUTS | {
    "genre_sf": "Подходит научная фантастика",
    "genre_detective": "Подходит детектив",
    "genre_fantasy": "Подходит фэнтези",
} | {f"candidate:{key}": f"Кандидат: {title}" for key, title in BOOKS.items()}

# Числа приоритета задаёт разработчик как учебную экспертную оценку.
# Внутри conditions действует И. Разные правила с одним заключением дают ИЛИ.
RULES = (
    Rule("R01", ("likes_science",), "genre_sf", 100),
    Rule("R02", ("likes_mystery",), "genre_detective", 100),
    Rule("R03", ("likes_magic",), "genre_fantasy", 100),
    Rule("R04", ("genre_sf",), "candidate:solaris", 40),
    Rule("R05", ("genre_sf", "likes_adventure"), "candidate:martian", 60),
    Rule("R06", ("genre_sf", "likes_philosophy"), "candidate:solaris", 60),
    Rule("R07", ("genre_detective",), "candidate:orient_express", 40),
    Rule("R08", ("genre_detective", "prefers_short"), "candidate:sherlock", 60),
    Rule("R09", ("genre_detective", "prefers_short", "prefers_classics"),
         "candidate:sherlock", 60),
    Rule("R10", ("genre_fantasy",), "candidate:earthsea", 40),
    Rule("R11", ("genre_fantasy", "likes_adventure"), "candidate:hobbit", 60),
    Rule("R12", ("genre_fantasy", "likes_philosophy"), "candidate:earthsea", 60),
)


def rank(rule: Rule, position: int) -> tuple[int, int, int]:
    """Меньший ключ лучше: приоритет, специфичность, порядок в базе."""
    return (-rule.priority, -len(rule.conditions), position)


def ordered(rules=RULES) -> list[Rule]:
    return [rule for _, rule in sorted(enumerate(rules),
                                      key=lambda pair: rank(pair[1], pair[0]))]


def make_facts(answers: dict[str, bool]) -> set[str]:
    unknown = set(answers) - INPUTS.keys()
    if unknown:
        raise ValueError(f"Неизвестные признаки: {sorted(unknown)}")
    if any(type(value) is not bool for value in answers.values()):
        raise ValueError("Ответ должен быть True или False")
    return {key for key, value in answers.items() if value}


def candidate_ids(memory: set[str]) -> set[str]:
    return {fact.split(":", 1)[1] for fact in memory if fact.startswith("candidate:")}


def select_book(memory: set[str], rules=RULES) -> tuple[str | None, str | None]:
    """Сравнить лучшие применимые обоснования всех выведенных кандидатов."""
    for rule in ordered(rules):
        if (rule.conclusion.startswith("candidate:")
                and rule.conclusion in memory
                and set(rule.conditions) <= memory):
            return rule.conclusion.split(":", 1)[1], rule.id
    return None, None


def describe(fact: str) -> str:
    return LABELS.get(fact, fact)
