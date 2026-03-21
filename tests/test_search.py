"""State-space search tests: weighted graph A* pathfinding.

Five nodes (A, B, C, D, E) with weighted edges.
Optimal A->E path: A->B->C->D->E, cost 7.
"""

import pytest

from epistemic_pipeline.encodings.search import (
    SearchBeliefs,
    SearchNode,
    SearchOntology,
    SearchOperator,
    SearchProblem,
    run_search_pipeline,
    search_update,
)
from epistemic_pipeline.meta import MetaDecision
from epistemic_pipeline.state import Observation

# ---------------------------------------------------------------------------
# Test graph helpers
# ---------------------------------------------------------------------------

def _graph_operators() -> tuple[SearchOperator, ...]:
    """Build operators for: A-B:1, A-C:4, B-C:2, B-D:5, C-D:1, D-E:3."""
    edges = [
        ("A", "B", 1.0),
        ("A", "C", 4.0),
        ("B", "C", 2.0),
        ("B", "D", 5.0),
        ("C", "D", 1.0),
        ("D", "E", 3.0),
    ]
    ops: list[SearchOperator] = []
    for src, dst, cost in edges:
        ops.append(SearchOperator(
            name=f"{src}_to_{dst}",
            applicable=lambda s, _src=src: s == _src,
            apply=lambda _s, _dst=dst: _dst,
            cost=lambda _s, _c=cost: _c,
        ))
        ops.append(SearchOperator(
            name=f"{dst}_to_{src}",
            applicable=lambda s, _dst=dst: s == _dst,
            apply=lambda _s, _src=src: _src,
            cost=lambda _s, _c=cost: _c,
        ))
    return tuple(ops)


def _heuristic(state: str) -> float:
    """Admissible h: h(A)=6, h(B)=5, h(C)=3, h(D)=3, h(E)=0."""
    return {"A": 6.0, "B": 5.0, "C": 3.0, "D": 3.0, "E": 0.0}.get(state, 0.0)


def _graph_problem() -> SearchProblem:
    """Full A->E pathfinding problem."""
    states = frozenset({"A", "B", "C", "D", "E"})
    return SearchProblem(
        states=states,
        operators=_graph_operators(),
        goal_test=lambda s: s == "E",
        heuristic=_heuristic,
        initial_state="A",
        max_search_steps=1000,
    )


# ---------------------------------------------------------------------------
# TestSearchTypes
# ---------------------------------------------------------------------------

class TestSearchTypes:
    """Search frozen dataclasses are immutable."""

    def test_operator_is_frozen(self):
        op = SearchOperator(
            name="test",
            applicable=lambda _s: True,
            apply=lambda s: s,
            cost=lambda _s: 1.0,
        )
        try:
            op.name = "other"  # type: ignore[misc]
        except (AttributeError, TypeError):
            pass
        else:
            raise AssertionError("SearchOperator should be frozen")

    def test_ontology_is_frozen(self):
        ontology = SearchOntology(
            states=frozenset({"A"}),
            operators=(),
            goal_test=lambda s: s == "A",
            heuristic=lambda _s: 0.0,
        )
        try:
            ontology.states = frozenset()  # type: ignore[misc]
        except (AttributeError, TypeError):
            pass
        else:
            raise AssertionError("SearchOntology should be frozen")

    def test_beliefs_is_frozen(self):
        beliefs = SearchBeliefs(frontier=(), explored=frozenset())
        try:
            beliefs.best_path = ("A",)  # type: ignore[misc]
        except (AttributeError, TypeError):
            pass
        else:
            raise AssertionError("SearchBeliefs should be frozen")

    def test_node_is_frozen(self):
        node = SearchNode(state="A", path=(), cost=0.0, priority=6.0)
        try:
            node.cost = 99.0  # type: ignore[misc]
        except (AttributeError, TypeError):
            pass
        else:
            raise AssertionError("SearchNode should be frozen")


# ---------------------------------------------------------------------------
# TestSearchOntologyAdequacy
# ---------------------------------------------------------------------------

class TestSearchOntologyAdequacy:
    """SearchOntology.adequate(E) checks state coverage."""

    def test_adequate_known_states(self):
        ontology = SearchOntology(
            states=frozenset({"A", "B"}),
            operators=(),
            goal_test=lambda _s: False,
            heuristic=lambda _s: 0.0,
        )
        evidence = (
            Observation(variable="A", value="visited", source="planner", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is True

    def test_inadequate_unknown_state(self):
        ontology = SearchOntology(
            states=frozenset({"A", "B"}),
            operators=(),
            goal_test=lambda _s: False,
            heuristic=lambda _s: 0.0,
        )
        evidence = (
            Observation(variable="Z", value="visited", source="planner", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is False

    def test_adequate_empty_evidence(self):
        ontology = SearchOntology(
            states=frozenset({"A"}),
            operators=(),
            goal_test=lambda _s: False,
            heuristic=lambda _s: 0.0,
        )
        assert ontology.adequate(()) is True

    def test_adequate_skips_search_step(self):
        ontology = SearchOntology(
            states=frozenset({"A"}),
            operators=(),
            goal_test=lambda _s: False,
            heuristic=lambda _s: 0.0,
        )
        # search_step is synthetic — not a real state name
        evidence = (
            Observation(variable="search_step", value="expand", source="planner", timestamp=0.0),
            Observation(variable="A", value="visited", source="planner", timestamp=1.0),
        )
        assert ontology.adequate(evidence) is True


# ---------------------------------------------------------------------------
# TestSearchUpdate
# ---------------------------------------------------------------------------

class TestSearchUpdate:
    """search_update does one A* expansion step."""

    def _simple_ontology(self) -> SearchOntology:
        ops = (
            SearchOperator(
                name="A_to_B",
                applicable=lambda s: s == "A",
                apply=lambda _s: "B",
                cost=lambda _s: 1.0,
            ),
            SearchOperator(
                name="A_to_C",
                applicable=lambda s: s == "A",
                apply=lambda _s: "C",
                cost=lambda _s: 4.0,
            ),
        )
        return SearchOntology(
            states=frozenset({"A", "B", "C"}),
            operators=ops,
            goal_test=lambda s: s == "C",
            heuristic=lambda _s: 0.0,
        )

    def _step_obs(self) -> Observation:
        return Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=0.0,
        )

    def test_expansion_adds_successors(self):
        ontology = self._simple_ontology()
        initial_node = SearchNode(state="A", path=(), cost=0.0, priority=0.0)
        beliefs = SearchBeliefs(
            frontier=(initial_node,),
            explored=frozenset(),
        )
        updated = search_update(beliefs, self._step_obs(), ontology)
        # A is now explored; B and C are on the frontier
        assert "A" in updated.explored
        frontier_states = {n.state for n in updated.frontier}
        assert "B" in frontier_states
        assert "C" in frontier_states

    def test_goal_found_records_path(self):
        ontology = self._simple_ontology()
        # Place a node pointing directly at the goal state
        goal_node = SearchNode(state="C", path=("A", "C"), cost=4.0, priority=4.0)
        beliefs = SearchBeliefs(
            frontier=(goal_node,),
            explored=frozenset(),
        )
        updated = search_update(beliefs, self._step_obs(), ontology)
        assert updated.best_path is not None
        assert updated.best_path[-1] == "C"
        assert updated.best_cost == pytest.approx(4.0)

    def test_empty_frontier_returns_unchanged(self):
        ontology = self._simple_ontology()
        beliefs = SearchBeliefs(frontier=(), explored=frozenset())
        updated = search_update(beliefs, self._step_obs(), ontology)
        assert updated == beliefs


# ---------------------------------------------------------------------------
# TestPathfindingPipeline
# ---------------------------------------------------------------------------

class TestPathfindingPipeline:
    """End-to-end: weighted graph finds optimal A->E path."""

    def test_finds_optimal_path(self):
        result = run_search_pipeline(_graph_problem())
        path = result.final_state.beliefs.best_path
        assert path == ("A", "B", "C", "D", "E")

    def test_optimal_cost(self):
        result = run_search_pipeline(_graph_problem())
        cost = result.final_state.beliefs.best_cost
        assert cost == pytest.approx(7.0)

    def test_goal_reached(self):
        result = run_search_pipeline(_graph_problem())
        assert result.final_state.beliefs.best_path is not None

    def test_trace_preserved(self):
        result = run_search_pipeline(_graph_problem())
        # Frame + 5 stages = 6 states in trace
        assert len(result.trace) == 6

    def test_meta_returns_accept(self):
        result = run_search_pipeline(_graph_problem())
        assert result.meta_decision.decision == MetaDecision.ACCEPT

    def test_evidence_records_search_steps(self):
        result = run_search_pipeline(_graph_problem())
        evidence = result.final_state.evidence
        assert len(evidence) > 0
        for obs in evidence:
            assert obs.variable == "search_step"


# ---------------------------------------------------------------------------
# TestSearchEdgeCases
# ---------------------------------------------------------------------------

class TestSearchEdgeCases:
    """Edge cases: unreachable goals and empty frontiers."""

    def test_unreachable_goal_flags_empty_frontier(self):
        # Two disconnected nodes; goal is unreachable from start
        problem = SearchProblem(
            states=frozenset({"A", "B"}),
            operators=(),          # no edges at all
            goal_test=lambda s: s == "B",
            heuristic=lambda _s: 0.0,
            initial_state="A",
            max_search_steps=10,
        )
        result = run_search_pipeline(problem)
        assert "empty_frontier" in result.final_state.metadata.anomalies

    def test_empty_frontier_returns_unchanged(self):
        ontology = SearchOntology(
            states=frozenset({"A"}),
            operators=(),
            goal_test=lambda s: s == "B",
            heuristic=lambda _s: 0.0,
        )
        beliefs = SearchBeliefs(frontier=(), explored=frozenset())
        obs = Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=0.0,
        )
        updated = search_update(beliefs, obs, ontology)
        assert updated == beliefs
