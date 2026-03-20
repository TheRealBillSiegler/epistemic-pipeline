"""STRIPS planning tests: blocks world scenario.

Two blocks (A, B) on a table. Goal: stack A on B.
Expected plan: [pickup_a, stack_a_b].
"""

from epistemic_pipeline.encodings.strips import (
    STRIPSAction,
    STRIPSBeliefs,
    STRIPSOntology,
    STRIPSProblem,
    run_strips_pipeline,
    strips_update,
)
from epistemic_pipeline.meta import MetaDecision
from epistemic_pipeline.state import Observation


def _blocks_world() -> STRIPSProblem:
    """Two blocks on a table. Goal: A on top of B."""
    predicates = frozenset({
        "on_table_A", "on_table_B", "clear_A", "clear_B",
        "on_A_B", "holding_A",
    })

    pickup_a = STRIPSAction(
        name="pickup_a",
        preconditions=frozenset({"on_table_A", "clear_A"}),
        add_effects=frozenset({"holding_A"}),
        delete_effects=frozenset({"on_table_A", "clear_A"}),
    )
    stack_a_b = STRIPSAction(
        name="stack_a_b",
        preconditions=frozenset({"holding_A", "clear_B"}),
        add_effects=frozenset({"on_A_B"}),
        delete_effects=frozenset({"holding_A", "clear_B"}),
    )

    initial_state = frozenset({"on_table_A", "on_table_B", "clear_A", "clear_B"})
    goal = frozenset({"on_A_B"})

    return STRIPSProblem(
        predicates=predicates,
        actions=(pickup_a, stack_a_b),
        goal=goal,
        initial_state=initial_state,
    )


class TestSTRIPSTypes:
    """STRIPS frozen dataclasses are immutable."""

    def test_action_is_frozen(self):
        action = STRIPSAction(
            name="a", preconditions=frozenset(), add_effects=frozenset(),
            delete_effects=frozenset(),
        )
        try:
            action.name = "b"  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("STRIPSAction should be frozen")

    def test_ontology_is_frozen(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}),
            actions=(),
            goal=frozenset({"p"}),
        )
        try:
            ontology.goal = frozenset()  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("STRIPSOntology should be frozen")

    def test_beliefs_is_frozen(self):
        beliefs = STRIPSBeliefs(current_state=frozenset({"p"}), plan=())
        try:
            beliefs.plan = ("a",)  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("STRIPSBeliefs should be frozen")


class TestSTRIPSOntologyAdequacy:
    """STRIPSOntology.adequate(E) checks predicate coverage."""

    def test_adequate_when_all_predicates_known(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p", "q"}), actions=(), goal=frozenset(),
        )
        evidence = (
            Observation(variable="p", value="true", source="init", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is True

    def test_inadequate_when_unknown_predicate(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset(),
        )
        evidence = (
            Observation(variable="unknown", value="true", source="init", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is False

    def test_adequate_with_empty_evidence(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset(),
        )
        assert ontology.adequate(()) is True


class TestSTRIPSUpdate:
    """strips_update does one frontier expansion step."""

    def test_goal_reached_returns_plan(self):
        problem = _blocks_world()
        ontology = STRIPSOntology(
            predicates=problem.predicates,
            actions=problem.actions,
            goal=problem.goal,
        )
        goal_state = frozenset({"on_table_B", "on_A_B"})
        beliefs = STRIPSBeliefs(
            current_state=problem.initial_state,
            plan=("pickup_a", "stack_a_b"),
            frontier=((goal_state, ("pickup_a", "stack_a_b")),),
            explored=frozenset(),
        )
        step_obs = Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=1.0,
        )
        updated = strips_update(beliefs, step_obs, ontology)
        assert ontology.goal.issubset(updated.current_state)

    def test_expansion_adds_successor_states(self):
        problem = _blocks_world()
        ontology = STRIPSOntology(
            predicates=problem.predicates,
            actions=problem.actions,
            goal=problem.goal,
        )
        beliefs = STRIPSBeliefs(
            current_state=problem.initial_state,
            plan=(),
            frontier=((problem.initial_state, ()),),
            explored=frozenset(),
        )
        step_obs = Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=1.0,
        )
        updated = strips_update(beliefs, step_obs, ontology)
        assert problem.initial_state in updated.explored
        assert len(updated.frontier) > 0


class TestBlocksWorldPipeline:
    """End-to-end: blocks world finds plan [pickup_a, stack_a_b]."""

    def test_finds_correct_plan(self):
        result = run_strips_pipeline(_blocks_world())
        plan = result.final_state.beliefs.plan
        assert plan == ("pickup_a", "stack_a_b")

    def test_goal_is_satisfied(self):
        result = run_strips_pipeline(_blocks_world())
        goal = result.final_state.ontology.goal
        assert goal.issubset(result.final_state.beliefs.current_state)

    def test_trace_preserved(self):
        result = run_strips_pipeline(_blocks_world())
        assert len(result.trace) == 6

    def test_meta_returns_accept(self):
        result = run_strips_pipeline(_blocks_world())
        assert result.meta_decision.decision == MetaDecision.ACCEPT

    def test_evidence_records_search_steps(self):
        result = run_strips_pipeline(_blocks_world())
        assert len(result.final_state.evidence) > 0
        for obs in result.final_state.evidence:
            assert obs.variable == "search_step"


class TestSTRIPSEdgeCases:
    """Edge cases: unsolvable problems, empty frontier, search_step adequacy."""

    def test_unsolvable_problem_flags_empty_frontier(self):
        problem = STRIPSProblem(
            predicates=frozenset({"p", "q"}),
            actions=(),
            goal=frozenset({"q"}),
            initial_state=frozenset({"p"}),
            max_search_steps=10,
        )
        result = run_strips_pipeline(problem)
        assert "empty_frontier" in result.final_state.metadata.anomalies

    def test_strips_update_empty_frontier_returns_unchanged(self):
        beliefs = STRIPSBeliefs(
            current_state=frozenset({"p"}), plan=(), frontier=(), explored=frozenset(),
        )
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset({"q"}),
        )
        obs = Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=0.0,
        )
        updated = strips_update(beliefs, obs, ontology)
        assert updated == beliefs

    def test_adequate_skips_search_step_observations(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset(),
        )
        evidence = (
            Observation(variable="search_step", value="expand", source="planner", timestamp=0.0),
            Observation(variable="p", value="true", source="init", timestamp=1.0),
        )
        assert ontology.adequate(evidence) is True
