"""Прямой и обратный вывод. Этот модуль не зависит от CLIPS."""
from dataclasses import dataclass
from knowledge import Rule, RULES, ordered


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
