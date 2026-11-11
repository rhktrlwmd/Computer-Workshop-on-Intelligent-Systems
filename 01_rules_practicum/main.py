"""Подбор книг: правила, два вида вывода, CLIPS и примеры в одном файле.
Запуск: python main.py --case 1 --framework --verbose
Проверки: python main.py --test
"""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import unittest

# 1. БАЗА ЗНАНИЙ И СТРАТЕГИЯ КОНФЛИКТОВ

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


# 2. ПРЯМОЙ И ОБРАТНЫЙ ВЫВОД БЕЗ ФРЕЙМВОРКА

@dataclass(frozen=True)
class Step:
    conflict_set: tuple[str, ...]
    fired: str
    added: str


def forward(initial: set[str], rules=RULES) -> tuple[set[str], list[Step]]:
    """Полный прямой вывод до неподвижной точки с протоколом конфликтов."""
    memory = set(initial)
    rules = ordered(rules)
    steps = []
    while True:
        agenda = [rule for rule in rules
                  if rule.conclusion not in memory
                  and set(rule.conditions) <= memory]
        if not agenda:
            return memory, steps
        selected = agenda[0]
        steps.append(Step(tuple(rule.id for rule in agenda),
                          selected.id, selected.conclusion))
        memory.add(selected.conclusion)


@dataclass(frozen=True)
class Proof:
    goal: str
    rule: str | None = None
    children: tuple["Proof", ...] = ()

    def lines(self, depth=0) -> list[str]:
        source = self.rule or "исходный факт"
        result = ["  " * depth + f"{self.goal} [{source}]"]
        for child in self.children:
            result.extend(child.lines(depth + 1))
        return result


def backward(goal: str, initial: set[str], rules=RULES,
             log: list[str] | None = None) -> Proof | None:
    """AND внутри правила, OR между правилами, возврат при неудаче ветви."""
    # Здесь передаются только исходные факты, а не результат forward().
    memory = set(initial)
    rules = ordered(rules)

    def say(depth, message):
        if log is not None:
            log.append("  " * depth + message)

    def prove(current: str, path: frozenset[str], depth: int) -> Proof | None:
        say(depth, f"Проверяем {current}")
        if current in memory:
            say(depth, "Есть в исходных фактах")
            return Proof(current)
        if current in path:
            say(depth, "Цикл в текущей ветви: пробуем другие правила")
            return None
        alternatives = [r for r in rules if r.conclusion == current]
        if not alternatives:
            say(depth, "Нет исходного факта и правила для его получения")
        for rule in alternatives:
            say(depth, f"Пробуем {rule.id}: нужны {', '.join(rule.conditions) or 'TRUE'}")
            children = []
            for condition in rule.conditions:
                proof = prove(condition, path | {current}, depth + 1)
                if proof is None:
                    say(depth, f"{rule.id}: условие {condition} не доказано")
                    break
                children.append(proof)
            else:
                say(depth, f"Доказано правилом {rule.id}")
                return Proof(current, rule.id, tuple(children))
        return None

    return prove(goal, frozenset(), 0)


# 3. ПРЯМОЙ И ОБРАТНЫЙ ВЫВОД С CLIPS

def clips_constructs() -> list[str]:
    blocks = [
        '(deftemplate known (slot value (type STRING)))',
        '(deftemplate fired (slot rule (type STRING)) (slot added (type STRING)))',
        '(deftemplate selected (slot book (type STRING)) (slot reason (type STRING)))',
    ]
    for index, rule in enumerate(ordered()):
        # Уникальные значения salience сохраняют всю составную стратегию.
        conditions = "\n  ".join(
            f"(known (value {json.dumps(fact)}))" for fact in rule.conditions)
        conclusion = json.dumps(rule.conclusion)
        blocks.append(f'''(defrule {rule.id}
  (declare (salience {1000 - index}))
  {conditions}
  (not (known (value {conclusion})))
  =>
  (assert (known (value {conclusion})))
  (assert (fired (rule "{rule.id}") (added {conclusion}))))''')
        if rule.conclusion.startswith("candidate:"):
            book = rule.conclusion.split(":", 1)[1]
            # Отрицательные salience: выбор только после всех правил вывода.
            blocks.append(f'''(defrule select-{rule.id}
  (declare (salience {-1000 - index}))
  {conditions}
  (known (value {conclusion}))
  (not (selected))
  =>
  (assert (selected (book "{book}") (reason "{rule.id}"))))''')
    return blocks


def clips_source() -> str:
    """Представление правил CLIPS для просмотра; отдельный файл не требуется."""
    return "\n\n".join(clips_constructs()) + "\n"


def run_clips(initial: set[str]):
    try:
        import clips
    except ImportError as exc:
        raise RuntimeError("Для CLIPS выполните: python -m pip install clipspy==1.0.6") from exc
    env = clips.Environment()
    for construct in clips_constructs():
        env.build(construct)
    env.reset()
    known = env.find_template("known")
    for value in sorted(initial):
        known.assert_fact(value=value)
    trace = []
    seen_log_indexes = set()
    while True:
        names = tuple(activation.name for activation in env.activations()
                      if not activation.name.startswith("select-"))
        if env.run(1) == 0:
            break
        for fact in env.facts():
            if fact.template.name == "fired" and fact.index not in seen_log_indexes:
                trace.append(Step(names, str(fact["rule"]), str(fact["added"])))
                seen_log_indexes.add(fact.index)
    memory, selected, reason = set(), None, None
    for fact in env.facts():
        if fact.template.name == "known":
            memory.add(str(fact["value"]))
        elif fact.template.name == "selected":
            selected, reason = str(fact["book"]), str(fact["reason"])
    return memory, trace, (selected, reason)


def run_clips_backward(goal: str, initial: set[str], rules=RULES,
                       log: list[str] | None = None) -> Proof | None:
    """Обратный поиск выполняет prove-goal в backward.clp, без forward()."""
    try:
        import clips
    except ImportError as exc:
        raise RuntimeError("Для CLIPS выполните: python -m pip install clipspy==1.0.6") from exc
    env = clips.Environment()
    env.load(str(Path(__file__).with_name("backward.clp")))
    env.reset()
    env.fact_duplication = True  # Сохранять повторные события разных ветвей поиска.
    known = env.find_template("bc-known")
    for value in sorted(initial):
        known.assert_fact(value=value)
    kb_rule = env.find_template("bc-rule")
    for position, rule in enumerate(ordered(rules)):
        kb_rule.assert_fact(rank=position, name=rule.id,
                            conclusion=rule.conclusion, conditions=rule.conditions)
    # Только целевой поиск: env.run() и Python backward() здесь не вызываются.
    root = env.call("prove-goal", goal)
    nodes = {}
    for fact in env.facts():
        if fact.template.name == "bc-proof":
            nodes[fact.index] = (str(fact["goal"]), str(fact["rule"]) or None,
                                 tuple(fact["children"]))
        elif log is not None and fact.template.name == "bc-event":
            log.append("  " * int(fact["depth"]) + str(fact["message"]))

    def read_proof(index):
        fact_goal, rule_id, children = nodes[index]
        return Proof(fact_goal, rule_id, tuple(read_proof(child) for child in children))

    return read_proof(root) if root else None


# 4. ДЕВЯТЬ ПРИМЕРОВ

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


# 5. ЗАПУСК И ВЫВОД РЕЗУЛЬТАТОВ

def show(example, use_framework=False, goal_override=None, verbose=False):
    initial = set(example.facts)
    print(f"\n{'=' * 64}\n{example.title}")
    print("Исходные факты:")
    for fact in sorted(initial):
        print(f"  {fact}: {describe(fact)}")
    if not initial:
        print("  Пустое множество")
    memory, steps = forward(initial)
    print("Прямой вывод:")
    for number, step in enumerate(steps, 1):
        print(f"  Шаг {number}. Конфликтное множество: {', '.join(step.conflict_set)}")
        print(f"    Выбрано {step.fired}. Новый факт: {step.added}")
    if not steps:
        print("  Нет применимых правил")
    print("Кандидаты:")
    for book in sorted(candidate_ids(memory)):
        print("  " + BOOKS[book])
    chosen = select_book(memory)
    print("Итог: " + (f"{BOOKS[chosen[0]]}, обоснование {chosen[1]}"
                      if chosen[0] else "Недостаточно данных для рекомендации"))
    goal = goal_override or example.goal
    log = []
    # Независимый запуск: только initial, без памяти прямого вывода.
    proof = backward(f"candidate:{goal}", initial, log=log)
    print(f"Обратный вывод. Цель: {BOOKS[goal]}")
    if proof:
        print("  Цель доказана. Дерево доказательства:")
        for line in proof.lines():
            print("  " + line)
    else:
        print("  Цель не доказана по имеющимся фактам и правилам.")
    if verbose or proof is None:
        print("Попытки обратного вывода:")
        for line in log:
            print("  " + line)
    if use_framework:
        clips_memory, clips_trace, clips_choice = run_clips(initial)
        if (clips_memory, clips_trace, clips_choice) != (memory, steps, chosen):
            raise RuntimeError("Обнаружено расхождение Python и CLIPS")
        print("CLIPS: факты, конфликтные множества, порядок правил и выбор совпадают.")
        clips_log = []
        clips_proof = run_clips_backward(f"candidate:{goal}", initial, log=clips_log)
        if clips_proof != proof:
            raise RuntimeError("Обнаружено расхождение обратного вывода Python и CLIPS")
        print("Обратный вывод CLIPS: " + ("цель доказана" if clips_proof else "цель не доказана"))
        if clips_proof:
            for line in clips_proof.lines():
                print("  " + line)
        if verbose or clips_proof is None:
            print("Попытки обратного вывода CLIPS:")
            for line in clips_log:
                print("  " + line)
        print("CLIPS: результат и дерево обратного доказательства совпадают с Python.")


def interactive():
    print("Ответьте на вопросы: да / нет. Нет означает, что признак не добавляется.")
    answers = {}
    for key, question in INPUTS.items():
        while True:
            answer = input(f"{question}? ").strip().lower()
            if answer in {"да", "д", "yes", "y", "нет", "н", "no", "n"}:
                answers[key] = answer in {"да", "д", "yes", "y"}
                break
            print("Введите да или нет")
    return Example("Собственные предпочтения", frozenset(make_facts(answers)),
                   "martian", None, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="все девять примеров")
    mode.add_argument("--case", type=int, choices=range(1, 10), help="один пример 1–9")
    mode.add_argument("--interactive", action="store_true", help="ввести предпочтения")
    mode.add_argument("--rules", action="store_true", help="показать базу знаний")
    parser.add_argument("--framework", action="store_true", help="сравнить с CLIPS")
    parser.add_argument("--goal", choices=BOOKS, help="книга для обратного вывода")
    parser.add_argument("--verbose", action="store_true", help="все попытки доказательства")
    mode.add_argument("--test", action="store_true", help="запустить все проверки")
    args = parser.parse_args()
    if args.test:
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent / "materials"))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if args.rules:
        for rule in RULES:
            condition = " И ".join(describe(x) for x in rule.conditions)
            print(f"{rule.id}: ЕСЛИ {condition}, ТО {describe(rule.conclusion)}. "
                  f"Приоритет {rule.priority}, условий {len(rule.conditions)}.")
        return
    if args.interactive:
        selected = [interactive()]
    elif args.case:
        selected = [EXAMPLES[args.case - 1]]
    else:
        selected = EXAMPLES
    for example in selected:
        show(example, args.framework, args.goal, args.verbose)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc))
