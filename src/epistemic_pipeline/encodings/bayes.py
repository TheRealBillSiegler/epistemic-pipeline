"""Bayesian encoding: hypotheses, likelihoods, Bayes' rule.

Expressiveness proof #1: probabilistic reasoning as an (O, E, B, R)
tuple. The ontology holds hypotheses and likelihood tables. Beliefs
are a probability distribution. The revision policy applies Bayes'
theorem to update beliefs given each observation.
"""

from dataclasses import dataclass, replace

from epistemic_pipeline.meta import MetaController
from epistemic_pipeline.pipeline import PipelineResult, run_pipeline
from epistemic_pipeline.state import EpistemicState, Metadata, Observation


@dataclass(frozen=True)
class BayesOntology:
    """Bayesian ontology: hypotheses, observables, and likelihood table.

    hypotheses: mutually exclusive hypothesis names (e.g. "flu", "cold").
    observables: names of things that can be observed (e.g. "fever").
    likelihoods: P(value | hypothesis, observable). Keyed by
        (hypothesis, observable, value) -> probability.
    """

    hypotheses: tuple[str, ...]
    observables: tuple[str, ...]
    likelihoods: dict[tuple[str, str, str], float]

    def adequate(self, evidence: "tuple[Observation, ...]") -> bool:
        """Check if this ontology covers all evidence.

        Returns True when every observation's (variable, value) pair
        has a likelihood entry for at least one hypothesis.

        Args:
            evidence: observations to check against this ontology.

        Returns:
            True if every observation is covered; False otherwise.
        """
        for obs in evidence:
            found = any(
                (h, obs.variable, obs.value) in self.likelihoods
                for h in self.hypotheses
            )
            if not found:
                return False
        return True


@dataclass(frozen=True)
class BayesBeliefs:
    """Probability distribution over hypotheses.

    probabilities: maps each hypothesis name to its probability.
    Invariant: sum(probabilities.values()) == 1.0 within float tolerance.
    """

    probabilities: dict[str, float]


def bayes_update(
    beliefs: BayesBeliefs,
    evidence: Observation,
    ontology: BayesOntology,
) -> BayesBeliefs:
    """Apply Bayes' rule for one observation: R(B, e, O) -> B'.

    P'(h) = P(e|h) * P(h) / sum_h'(P(e|h') * P(h')).

    Args:
        beliefs: current probability distribution over hypotheses.
        evidence: the observation (variable, value pair).
        ontology: contains the likelihood table.

    Returns:
        Updated BayesBeliefs with normalized posterior probabilities.
    """
    posteriors: dict[str, float] = {}
    total = 0.0

    for h in ontology.hypotheses:
        likelihood = ontology.likelihoods.get(
            (h, evidence.variable, evidence.value),
            0.0,
        )
        prior = beliefs.probabilities[h]
        unnormalized = likelihood * prior
        posteriors[h] = unnormalized
        total += unnormalized

    if total > 0:
        posteriors = {h: p / total for h, p in posteriors.items()}

    return BayesBeliefs(probabilities=posteriors)


def bayes_argmax(beliefs: BayesBeliefs) -> str:
    """Return the hypothesis with the highest probability.

    Args:
        beliefs: a Bayesian probability distribution.

    Returns:
        The name of the most probable hypothesis.
    """
    return max(beliefs.probabilities, key=lambda h: beliefs.probabilities[h])


# --- Pipeline stage functions ---


def bayes_frame(
    problem: BayesProblem,
) -> EpistemicState[BayesOntology, BayesBeliefs]:
    """Frame stage: build ontology and set prior beliefs.

    Constructs the BayesOntology from the problem specification.
    Sets uniform priors unless the problem provides custom priors.
    Stores pending observations in metadata for the Test stage.

    Args:
        problem: the full Bayesian inference problem specification.

    Returns:
        Initial EpistemicState ready for the pipeline.
    """
    ontology = BayesOntology(
        hypotheses=problem.hypotheses,
        observables=problem.observables,
        likelihoods=problem.likelihoods,
    )

    if problem.priors is None:
        n = len(problem.hypotheses)
        prior_dist = dict.fromkeys(problem.hypotheses, 1.0 / n)
    else:
        prior_dist = dict(problem.priors)

    beliefs = BayesBeliefs(probabilities=prior_dist)

    metadata = Metadata(
        strategy="bayesian",
        evidence_order=tuple(obs.variable for obs in problem.observations),
        pending_observations=problem.observations,
    )

    return EpistemicState(
        ontology=ontology,
        evidence=(),
        beliefs=beliefs,
        revision_policy=bayes_update,
        metadata=metadata,
    )


def bayes_decompose(
    state: EpistemicState[BayesOntology, BayesBeliefs],
) -> EpistemicState[BayesOntology, BayesBeliefs]:
    """Decompose stage: no-op for Bayesian inference.

    Bayesian updating does not require sub-problem decomposition.
    """
    return state


def bayes_model(
    state: EpistemicState[BayesOntology, BayesBeliefs],
) -> EpistemicState[BayesOntology, BayesBeliefs]:
    """Model stage: no-op. Priors and revision policy are set in Frame."""
    return state


def bayes_select(
    state: EpistemicState[BayesOntology, BayesBeliefs],
) -> EpistemicState[BayesOntology, BayesBeliefs]:
    """Select stage: evidence order is already set in Frame metadata."""
    return state


def bayes_test(
    state: EpistemicState[BayesOntology, BayesBeliefs],
) -> EpistemicState[BayesOntology, BayesBeliefs]:
    """Test stage: apply Bayes' rule for each pending observation.

    Processes observations in order. For each one, calls R(B, e, O)
    to get updated beliefs, then appends the observation to evidence.
    Clears pending_observations when done.
    """
    beliefs = state.beliefs
    evidence_list = list(state.evidence)

    for obs in state.metadata.pending_observations:
        beliefs = state.revision_policy(beliefs, obs, state.ontology)
        evidence_list.append(obs)

    return replace(
        state,
        beliefs=beliefs,
        evidence=tuple(evidence_list),
        metadata=replace(state.metadata, pending_observations=()),
    )


def bayes_integrate(
    state: EpistemicState[BayesOntology, BayesBeliefs],
) -> EpistemicState[BayesOntology, BayesBeliefs]:
    """Integrate stage: posterior is already in beliefs.

    In v0.1, integration is a pass-through. The posterior distribution
    is in state.beliefs. Future versions will add confidence metrics
    and explanation generation.
    """
    return state


@dataclass(frozen=True)
class BayesProblem:
    """Full specification of a Bayesian inference problem.

    hypotheses: mutually exclusive hypothesis names.
    observables: observable variable names.
    likelihoods: P(value | hypothesis, observable) lookup table.
    observations: evidence to process in the Test stage.
    priors: initial probability distribution. Uniform if None.
    """

    hypotheses: tuple[str, ...]
    observables: tuple[str, ...]
    likelihoods: dict[tuple[str, str, str], float]
    observations: tuple[Observation, ...]
    priors: dict[str, float] | None = None


def run_bayesian_pipeline(
    problem: BayesProblem,
    meta_controller: MetaController | None = None,
) -> PipelineResult[BayesOntology, BayesBeliefs]:
    """Run a complete Bayesian inference pipeline.

    Composes all six stages: Frame -> Decompose -> Model -> Select ->
    Test -> Integrate. Returns the result with full trace and
    meta-layer evaluation.

    Args:
        problem: the Bayesian inference problem specification.
        meta_controller: meta-epistemic controller. Defaults to v0.1 stub.

    Returns:
        PipelineResult with final state, trace, and meta decision.
    """
    initial_state = bayes_frame(problem)

    return run_pipeline(
        initial_state=initial_state,
        stages=[
            bayes_decompose,
            bayes_model,
            bayes_select,
            bayes_test,
            bayes_integrate,
        ],
        meta_controller=meta_controller,
    )
