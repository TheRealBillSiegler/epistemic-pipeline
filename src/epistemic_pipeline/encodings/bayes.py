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
    """Apply confidence-weighted Bayes' rule: R(B, e, O) -> B'.

    L_eff(e|h) = c * P(e|h) + (1 - c) * P(e)
    P'(h) = L_eff(e|h) * P(h) / sum_h'(L_eff(e|h') * P(h'))

    c is evidence.confidence. At c=1.0, this is standard Bayes.
    At c=0.0, L_eff equals the marginal for all h, so beliefs don't change.

    Args:
        beliefs: current probability distribution over hypotheses.
        evidence: the observation, including its confidence weight.
        ontology: contains the likelihood table.

    Returns:
        Updated BayesBeliefs with normalized posterior probabilities.
    """
    c = evidence.confidence

    # Raw likelihoods P(e|h)
    raw: dict[str, float] = {}
    for h in ontology.hypotheses:
        raw[h] = ontology.likelihoods.get(
            (h, evidence.variable, evidence.value), 0.0,
        )

    # Marginal P(e) = sum_h P(e|h) * P(h)
    marginal = sum(
        raw[h] * beliefs.probabilities[h] for h in ontology.hypotheses
    )

    # Effective likelihood: L_eff(e|h) = c * P(e|h) + (1 - c) * P(e)
    posteriors: dict[str, float] = {}
    total = 0.0
    for h in ontology.hypotheses:
        l_eff = c * raw[h] + (1.0 - c) * marginal
        unnormalized = l_eff * beliefs.probabilities[h]
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


def _detect_oscillation(confidence_history: list[float]) -> bool:
    """Check for oscillation: max-probability reverses direction >= 3 times.

    confidence_history contains the MAP probability after each evidence step.
    A direction reversal is when the MAP probability goes from rising to
    falling or vice versa. Three reversals in six steps means the evidence
    is pushing beliefs back and forth without convergence.

    Args:
        confidence_history: MAP probability after each evidence step.

    Returns:
        True if oscillation is detected; False otherwise.
    """
    window = confidence_history[-6:]
    if len(window) < 3:
        return False
    reversals = 0
    for i in range(1, len(window) - 1):
        prev_rising = window[i] > window[i - 1]
        next_rising = window[i + 1] > window[i]
        if prev_rising != next_rising:
            reversals += 1
    return reversals >= 3


def _detect_contradiction(
    obs: Observation,
    prior_evidence: tuple[Observation, ...],
    beliefs_before: BayesBeliefs,
    beliefs_after: BayesBeliefs,
) -> bool:
    """Check for contradiction after processing one observation.

    Two triggers:
    1. Same-variable conflict: another observation of this variable
       had a different value.
    2. High-confidence reversal: the old MAP had probability > 0.8,
       and that same hypothesis lost more than 0.3 probability after
       the update.

    Args:
        obs: the observation just processed.
        prior_evidence: all observations processed before this one.
        beliefs_before: beliefs before processing obs.
        beliefs_after: beliefs after processing obs.

    Returns:
        True if a contradiction is detected; False otherwise.
    """
    # Same-variable conflict
    for prev in prior_evidence:
        if prev.variable == obs.variable and prev.value != obs.value:
            return True

    # High-confidence reversal
    old_map = max(
        beliefs_before.probabilities,
        key=lambda h: beliefs_before.probabilities[h],
    )
    old_prob = beliefs_before.probabilities[old_map]
    new_prob = beliefs_after.probabilities[old_map]
    if old_prob > 0.8 and (old_prob - new_prob) > 0.3:
        return True

    return False


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
    Detects anomalies (oscillation and contradiction) after each update.
    Clears pending_observations when done.

    Args:
        state: current epistemic state with pending observations.

    Returns:
        Updated state with final beliefs, accumulated evidence, and anomalies.
    """
    beliefs = state.beliefs
    evidence_list = list(state.evidence)
    anomalies = list(state.metadata.anomalies)
    confidence_history: list[float] = []

    for obs in state.metadata.pending_observations:
        beliefs_before = beliefs
        beliefs = state.revision_policy(beliefs, obs, state.ontology)
        evidence_list.append(obs)
        map_prob = beliefs.probabilities[bayes_argmax(beliefs)]
        confidence_history.append(map_prob)

        if _detect_contradiction(
            obs, tuple(evidence_list[:-1]), beliefs_before, beliefs,
        ):
            anomalies.append("contradiction")

        if _detect_oscillation(confidence_history):
            anomalies.append("oscillation")

    return replace(
        state,
        beliefs=beliefs,
        evidence=tuple(evidence_list),
        metadata=replace(
            state.metadata,
            pending_observations=(),
            anomalies=tuple(anomalies),
        ),
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
