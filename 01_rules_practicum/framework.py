"""Настоящий вывод средствами CLIPS через clipspy."""
import json
from pathlib import Path
from knowledge import RULES, ordered
from engine import Step


def clips_source() -> str:
    blocks = [
        "; Сгенерировано из knowledge.py командой python framework.py",
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
    return "\n\n".join(blocks) + "\n"


def run_clips(initial: set[str]):
    try:
        import clips
    except ImportError as exc:
        raise RuntimeError("Для CLIPS выполните: python -m pip install -r requirements.txt") from exc
    env = clips.Environment()
    env.load(str(Path(__file__).with_name("books.clp")))
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


if __name__ == "__main__":
    target = Path(__file__).with_name("books.clp")
    target.write_text(clips_source(), encoding="utf-8")
    print(f"Обновлён файл {target.name}")
