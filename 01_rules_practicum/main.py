"""Консольная демонстрация всех трёх практических упражнений."""
import argparse
from knowledge import (BOOKS, INPUTS, RULES, describe, make_facts,
                       candidate_ids, select_book)
from engine import forward, backward
from examples import EXAMPLES, Example


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
        from framework import run_clips, run_clips_backward
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
    args = parser.parse_args()
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
