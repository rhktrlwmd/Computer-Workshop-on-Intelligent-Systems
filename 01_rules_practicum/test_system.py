"""Проверки алгоритмов, стратегии конфликтов и эквивалентности с CLIPS."""
import importlib.util
import itertools
from pathlib import Path
import unittest
from unittest.mock import patch
from engine import forward, backward
from examples import EXAMPLES
from knowledge import (BOOKS, INPUTS, RULES, Rule, make_facts,
                       select_book, candidate_ids)
from framework import clips_source, run_clips, run_clips_backward


def all_profiles():
    keys = tuple(INPUTS)
    for values in itertools.product((False, True), repeat=len(keys)):
        yield {key for key, value in zip(keys, values) if value}


class InferenceTests(unittest.TestCase):
    def test_examples(self):
        for example in EXAMPLES:
            with self.subTest(example=example.title):
                memory, _ = forward(set(example.facts))
                self.assertEqual(select_book(memory)[0], example.expected)
                self.assertEqual(backward(f"candidate:{example.goal}", set(example.facts))
                                 is not None, example.goal_proved)

    def test_priority(self):
        memory, steps = forward({"likes_science", "likes_adventure"})
        self.assertEqual(steps[1].conflict_set, ("R05", "R04"))
        self.assertEqual(steps[1].fired, "R05")
        self.assertEqual(select_book(memory), ("martian", "R05"))

    def test_specificity(self):
        memory, steps = forward({"likes_mystery", "prefers_short", "prefers_classics"})
        self.assertEqual(steps[1].conflict_set, ("R09", "R08", "R07"))
        self.assertEqual(steps[1].fired, "R09")
        self.assertEqual(select_book(memory), ("sherlock", "R09"))

    def test_order_breaks_tie(self):
        facts = {"likes_science", "likes_magic", "likes_adventure"}
        memory, _ = forward(facts)
        self.assertEqual(select_book(memory), ("martian", "R05"))
        swapped = list(RULES)
        swapped[4], swapped[10] = swapped[10], swapped[4]
        changed, _ = forward(facts, swapped)
        self.assertEqual(changed, memory)  # Замыкание сохраняется.
        self.assertEqual(select_book(changed, swapped), ("hobbit", "R11"))

    def test_forward_backward_all_128_profiles(self):
        for facts in all_profiles():
            memory, _ = forward(facts)
            for book in BOOKS:
                goal = f"candidate:{book}"
                with self.subTest(facts=sorted(facts), goal=goal):
                    self.assertEqual(goal in memory, backward(goal, facts) is not None)

    def test_no_input_mutation(self):
        initial = {"likes_science", "likes_adventure"}
        before = set(initial)
        forward(initial)
        backward("candidate:martian", initial)
        self.assertEqual(initial, before)

    def test_fixed_point(self):
        memory, _ = forward(set(INPUTS))
        repeated, steps = forward(memory)
        self.assertEqual(memory, repeated)
        self.assertEqual(steps, [])

    def test_and_requires_all_conditions(self):
        self.assertIsNone(backward("candidate:martian", {"likes_science"}))
        memory, _ = forward({"likes_science"})
        self.assertNotIn("martian", candidate_ids(memory))

    def test_or_alternative_after_failure(self):
        proof = backward("candidate:solaris", {"likes_science"})
        self.assertIsNotNone(proof)
        self.assertEqual(proof.rule, "R04")  # R06 не удалось доказать.

    def test_cycle_without_base(self):
        rules = (Rule("A", ("b",), "a", 1), Rule("B", ("a",), "b", 1))
        self.assertIsNone(backward("a", set(), rules))
        self.assertEqual(forward(set(), rules), (set(), []))

    def test_cycle_with_alternative(self):
        rules = (Rule("A", ("b",), "a", 10), Rule("B", ("a",), "b", 10),
                 Rule("C", ("seed",), "b", 1))
        proof = backward("a", {"seed"}, rules)
        self.assertIsNotNone(proof)
        self.assertIn("a", forward({"seed"}, rules)[0])

    def test_empty_conditions(self):
        rules = (Rule("F", (), "fact", 1),)
        self.assertIn("fact", forward(set(), rules)[0])
        self.assertIsNotNone(backward("fact", set(), rules))

    def test_backward_accepts_initial_goal(self):
        proof = backward("likes_science", {"likes_science"})
        self.assertIsNotNone(proof)
        self.assertIsNone(proof.rule)

    def test_empty_profile(self):
        memory, trace = forward(set())
        self.assertEqual((memory, trace, select_book(memory)), (set(), [], (None, None)))

    def test_true_false_and_unknown_input(self):
        self.assertEqual(make_facts({"likes_science": True, "likes_magic": False}),
                         {"likes_science"})
        with self.assertRaises(ValueError):
            make_facts({"unknown": True})
        with self.assertRaises(ValueError):
            make_facts({"likes_science": "да"})

    def test_no_duplicate_conclusions(self):
        _, steps = forward(set(INPUTS))
        self.assertEqual(len(steps), len({step.added for step in steps}))

    def test_generated_clips_is_current(self):
        self.assertEqual(Path(__file__).with_name("books.clp").read_text(encoding="utf-8"),
                         clips_source())


@unittest.skipUnless(importlib.util.find_spec("clips"), "clipspy не установлен")
class FrameworkTests(unittest.TestCase):
    def test_backward_all_128_profiles(self):
        for facts in all_profiles():
            for book in BOOKS:
                goal = f"candidate:{book}"
                with self.subTest(facts=sorted(facts), goal=goal):
                    self.assertEqual(run_clips_backward(goal, facts), backward(goal, facts))

    def test_backward_alternative_after_failure(self):
        log = []
        proof = run_clips_backward("candidate:solaris", {"likes_science"}, log=log)
        self.assertEqual(proof.rule, "R04")
        self.assertTrue(any("Пробуем R06" in line for line in log))
        self.assertTrue(any("Пробуем R04" in line for line in log))

    def test_backward_cycles(self):
        cycle = (Rule("A", ("b",), "a", 10), Rule("B", ("a",), "b", 10))
        self.assertIsNone(run_clips_backward("a", set(), cycle))
        rules = cycle + (Rule("C", ("seed",), "b", 1),)
        self.assertEqual(run_clips_backward("a", {"seed"}, rules),
                         backward("a", {"seed"}, rules))

    def test_backward_unconditional_rule(self):
        rules = (Rule("F", (), "fact", 1),)
        self.assertEqual(run_clips_backward("fact", set(), rules),
                         backward("fact", set(), rules))

    def test_backward_initial_goal(self):
        self.assertEqual(run_clips_backward("likes_science", {"likes_science"}),
                         backward("likes_science", {"likes_science"}))

    def test_backward_empty_rule_base(self):
        self.assertIsNone(run_clips_backward("unknown", set(), ()))

    def test_backward_independent_goal_search(self):
        facts = {"likes_science", "likes_adventure", "likes_magic"}
        before = set(facts)
        log = []
        with patch("engine.forward", side_effect=AssertionError("forward запрещён")), \
             patch("engine.backward", side_effect=AssertionError("Python backward запрещён")), \
             patch("framework.run_clips", side_effect=AssertionError("CLIPS forward запрещён")):
            proof = run_clips_backward("candidate:martian", facts, log=log)
        self.assertEqual(proof.rule, "R05")
        self.assertEqual(facts, before)
        self.assertFalse(any("Пробуем R03" in line or "Пробуем R11" in line for line in log))

    def test_backward_tries_another_branch_after_cycle(self):
        rules = (Rule("A", ("b", "c"), "goal", 10),
                 Rule("B", ("c",), "b", 10),
                 Rule("C", ("b",), "c", 10),
                 Rule("D", ("seed",), "b", 1))
        self.assertEqual(run_clips_backward("goal", {"seed"}, rules),
                         backward("goal", {"seed"}, rules))

    def test_all_128_profiles(self):
        for facts in all_profiles():
            with self.subTest(facts=sorted(facts)):
                memory, trace = forward(facts)
                self.assertEqual(run_clips(facts), (memory, trace, select_book(memory)))

    def test_examples(self):
        for example in EXAMPLES:
            with self.subTest(example=example.title):
                facts = set(example.facts)
                memory, trace, selected = run_clips(facts)
                self.assertEqual(selected[0], example.expected)
                self.assertEqual(candidate_ids(memory), candidate_ids(forward(facts)[0]))

    def test_clips_specificity_agenda(self):
        _, trace, _ = run_clips({"likes_mystery", "prefers_short", "prefers_classics"})
        self.assertEqual(trace[1].conflict_set, ("R09", "R08", "R07"))

    def test_clips_tie_order(self):
        _, _, selected = run_clips({"likes_science", "likes_magic", "likes_adventure"})
        self.assertEqual(selected, ("martian", "R05"))

    def test_clips_empty_profile(self):
        self.assertEqual(run_clips(set()), (set(), [], (None, None)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
