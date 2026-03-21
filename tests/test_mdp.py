"""MDP encoding tests: 4x3 grid world value iteration.

Russell & Norvig grid world. Goal: verify value iteration converges
to the correct policy and value function.
"""

import pytest

from epistemic_pipeline.encodings.mdp import (
    MDPBeliefs,
    MDPOntology,
    grid_world,
    mdp_update,
    run_mdp_pipeline,
)
from epistemic_pipeline.meta import MetaDecision
from epistemic_pipeline.state import Observation

# ---------------------------------------------------------------------------
# Minimal helpers
# ---------------------------------------------------------------------------

def _simple_ontology() -> MDPOntology:
    """Two-state MDP: s0 <-> s1."""
    states = frozenset({"s0", "s1"})
    actions = ("go",)
    transitions = {
        ("s0", "go", "s1"): 1.0,
        ("s1", "go", "s0"): 1.0,
    }
    rewards: dict[str, float] = {"s0": -1.0, "s1": 1.0}
    return MDPOntology(
        states=states,
        actions=actions,
        transitions=transitions,
        rewards=rewards,
        discount=0.9,
    )


def _simple_beliefs() -> MDPBeliefs:
    return MDPBeliefs(
        value_function={"s0": 0.0, "s1": 0.0},
        policy={"s0": "go", "s1": "go"},
    )


# ---------------------------------------------------------------------------
# TestMDPTypes
# ---------------------------------------------------------------------------

class TestMDPTypes:
    """MDPOntology and MDPBeliefs are immutable frozen dataclasses."""

    def test_ontology_is_frozen(self):
        ont = _simple_ontology()
        try:
            ont.discount = 0.5  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("MDPOntology should be frozen")

    def test_beliefs_is_frozen(self):
        b = _simple_beliefs()
        try:
            b.iteration = 99  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("MDPBeliefs should be frozen")


# ---------------------------------------------------------------------------
# TestMDPOntologyAdequacy
# ---------------------------------------------------------------------------

class TestMDPOntologyAdequacy:
    """MDPOntology.adequate() checks that observed variables are known states."""

    def test_adequate_known_states(self):
        ont = _simple_ontology()
        evidence = (
            Observation(variable="s0", value="visited", source="env", timestamp=0.0),
        )
        assert ont.adequate(evidence) is True

    def test_inadequate_unknown_state(self):
        ont = _simple_ontology()
        evidence = (
            Observation(variable="s_unknown", value="visited", source="env", timestamp=0.0),
        )
        assert ont.adequate(evidence) is False

    def test_adequate_empty_evidence(self):
        ont = _simple_ontology()
        assert ont.adequate(()) is True

    def test_adequate_skips_bellman_sweep(self):
        ont = _simple_ontology()
        # bellman_sweep obs plus a valid state obs — should be True.
        evidence = (
            Observation(variable="bellman_sweep", value="0", source="planner", timestamp=0.0),
            Observation(variable="s0", value="visited", source="env", timestamp=1.0),
        )
        assert ont.adequate(evidence) is True

    def test_adequate_skips_bellman_sweep_with_unknown(self):
        ont = _simple_ontology()
        # bellman_sweep skipped; but s_bad is not a known state.
        evidence = (
            Observation(variable="bellman_sweep", value="0", source="planner", timestamp=0.0),
            Observation(variable="s_bad", value="visited", source="env", timestamp=1.0),
        )
        assert ont.adequate(evidence) is False


# ---------------------------------------------------------------------------
# TestMDPGetReward
# ---------------------------------------------------------------------------

class TestMDPGetReward:
    """MDPOntology.get_reward() handles tuple keys, string keys, and missing."""

    def test_state_action_reward(self):
        """Rewards dict uses (state, action) tuple keys."""
        ont = MDPOntology(
            states=frozenset({"s0"}),
            actions=("a",),
            transitions={},
            rewards={("s0", "a"): 5.0},
            discount=0.9,
        )
        assert ont.get_reward("s0", "a") == pytest.approx(5.0)

    def test_state_only_reward(self):
        """Rewards dict uses plain string (state) keys."""
        ont = MDPOntology(
            states=frozenset({"s0"}),
            actions=("a",),
            transitions={},
            rewards={"s0": 3.0},
            discount=0.9,
        )
        assert ont.get_reward("s0", "a") == pytest.approx(3.0)

    def test_missing_reward_returns_zero(self):
        """Returns 0.0 when the state has no reward entry."""
        ont = MDPOntology(
            states=frozenset({"s0", "s1"}),
            actions=("a",),
            transitions={},
            rewards={"s0": 1.0},
            discount=0.9,
        )
        assert ont.get_reward("s1", "a") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestMDPUpdate
# ---------------------------------------------------------------------------

class TestMDPUpdate:
    """mdp_update performs one Bellman sweep."""

    def test_single_sweep_changes_values(self):
        ont = _simple_ontology()
        beliefs = _simple_beliefs()
        obs = Observation(
            variable="bellman_sweep", value="0", source="planner", timestamp=0.0,
        )
        updated = mdp_update(beliefs, obs, ont)
        # After one sweep with nonzero rewards, values must change.
        assert updated.value_function != beliefs.value_function

    def test_iteration_increments(self):
        ont = _simple_ontology()
        beliefs = _simple_beliefs()
        obs = Observation(
            variable="bellman_sweep", value="0", source="planner", timestamp=0.0,
        )
        updated = mdp_update(beliefs, obs, ont)
        assert updated.iteration == 1

    def test_convergence_detected(self):
        """After enough sweeps, the value function converges."""
        ont = _simple_ontology()
        beliefs = _simple_beliefs()
        obs = Observation(
            variable="bellman_sweep", value="0", source="planner", timestamp=0.0,
        )
        for _ in range(500):
            if beliefs.converged:
                break
            beliefs = mdp_update(beliefs, obs, ont)
        assert beliefs.converged is True


# ---------------------------------------------------------------------------
# TestGridWorldPipeline
# ---------------------------------------------------------------------------

class TestGridWorldPipeline:
    """End-to-end: 4x3 grid world converges to correct policy."""

    def test_converges(self):
        result = run_mdp_pipeline(grid_world())
        assert result.final_state.beliefs.converged is True

    def test_positive_terminal_has_highest_value(self):
        result = run_mdp_pipeline(grid_world())
        vf = result.final_state.beliefs.value_function
        assert vf["3_2"] == pytest.approx(max(vf.values()))

    def test_optimal_policy_avoids_negative(self):
        """From state 2_1, optimal policy should NOT go right into -1 terminal."""
        result = run_mdp_pipeline(grid_world())
        policy = result.final_state.beliefs.policy
        assert policy["2_1"] != "right"

    def test_trace_preserved(self):
        result = run_mdp_pipeline(grid_world())
        # Frame + 5 stages = 6 states in trace.
        assert len(result.trace) == 6

    def test_meta_returns_accept(self):
        result = run_mdp_pipeline(grid_world())
        assert result.meta_decision.decision == MetaDecision.ACCEPT


# ---------------------------------------------------------------------------
# TestMDPEdgeCases
# ---------------------------------------------------------------------------

class TestMDPEdgeCases:
    """Edge cases: convergence is sticky at the true fixed point."""

    def test_already_converged_stays_converged(self):
        """A value function at its fixed point stays converged after another sweep."""
        ont = _simple_ontology()
        beliefs = _simple_beliefs()
        obs = Observation(
            variable="bellman_sweep", value="0", source="planner", timestamp=0.0,
        )
        # Run until converged.
        for _ in range(500):
            if beliefs.converged:
                break
            beliefs = mdp_update(beliefs, obs, ont)

        assert beliefs.converged is True

        # One more sweep on an already-converged state must still be converged.
        updated = mdp_update(beliefs, obs, ont)
        assert updated.converged is True
