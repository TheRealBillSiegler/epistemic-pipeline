# The encodings

**An encoding is a way of filling in the four slots `(O, E, B, R)` for one reasoning framework.** Bayesian inference, classical planning, graph search, and Markov decision processes each become an epistemic pipeline once you say what counts as O, E, B, and R for them. The first five encodings below exist to prove the tuple can hold any of these frameworks. They are demonstrations, not products. The sixth, worldview, is the one being built into a real application — see [The worldview app](../worldview/index.md).

## What each encoding proves

| Encoding | O becomes | E becomes | B becomes | R becomes | What it demonstrates |
|---|---|---|---|---|---|
| [Bayes](#bayes) | hypotheses + likelihood table | one observed variable/value pair per step | a probability distribution over hypotheses | Bayes' theorem | classic probabilistic updating fits the tuple |
| [STRIPS](#strips) | predicates, actions, goal | one search-step signal per expansion | current state, plan, and search frontier | expand one frontier state per call | planning — choosing actions, not just rating beliefs — fits the tuple |
| [Search](#search) | states, operators, goal test, heuristic | one search-step signal per expansion | the A* frontier, explored set, best path | expand the best frontier node (A*) | pathfinding is an epistemic process too: each expansion is a belief about the best route |
| [MDP](#mdp) | state space, actions, transitions, rewards | one synthetic observation per Bellman sweep | the value function and derived policy | one Bellman sweep | sequential decision-making under uncertainty fits the tuple |
| [LLM-agent](#llm-agent) | a closed set of hypotheses + tool names | tool results and LLM confidence reports | a confidence distribution over hypotheses | parse the LLM's latest confidence vector, renormalize | an LLM tool-calling loop — the thing most engineers actually build — fits the tuple |
| [Worldview](#worldview) | claim identifiers seen in a document corpus | one LLM confidence vector per document | a [Subjective Logic opinion](../beliefs/opinions.md) per claim | discount by source reliability, accumulate into each opinion | the one encoding being shipped as a product |

Every row keeps the same invariants from [the state tuple](state.md): O is static within a run, E is append-only, R is pure. The math inside R differs; the contract around it does not.

## Bayes

*Expressiveness proof #1.* The ontology holds a set of mutually exclusive hypotheses (for example `flu`, `cold`) and a likelihood table: how probable each observation is under each hypothesis. Beliefs are a probability distribution that must sum to 1. The revision policy applies Bayes' theorem: given one new observation, it reweights every hypothesis by how well that hypothesis predicted the observation. This is the textbook case, included because if the tuple cannot hold Bayesian updating, it cannot hold anything built on top of it.

Source: [`bayes.py`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/bayes.py).

## STRIPS

*Expressiveness proof #2.* STRIPS (Stanford Research Institute Problem Solver) is a classical planning formalism: given a start state, a goal, and a set of actions with preconditions and effects, find a sequence of actions that reaches the goal. Here the goal itself lives in O — it is a fixed commitment about the problem, not something evidence can move. Beliefs track the current state, the plan so far, and the search frontier. R expands one frontier state per call, one action at a time. This shows the tuple can hold planning, where the "belief" being revised is a course of action, not a confidence number.

Source: [`strips.py`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/strips.py).

## Search

*Expressiveness proof #3.* This encoding runs A* pathfinding — a graph-search algorithm that finds the cheapest path to a goal using a cost-so-far plus a heuristic estimate of cost-to-go. The ontology holds the state graph, the operators that move between states, a goal test, and the heuristic function. Beliefs are the frontier of unexplored nodes, the set already explored, and the best path found so far. R expands the most promising frontier node each step. Framing search this way makes a concrete point: every node expansion is a small belief revision about which partial path is worth pursuing.

Source: [`search.py`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/search.py).

## MDP

*Expressiveness proof #4.* An MDP (Markov Decision Process) models sequential decisions under uncertainty: a set of states, actions, probabilistic transitions between states, and rewards. The ontology holds all of that structure. Beliefs are the value function — an estimate of how good each state is — plus the policy derived from it. R runs one Bellman sweep per call: value iteration's standard update, which refines every state's value estimate using its neighbors. Each sweep is treated as a synthetic observation, so even an algorithm with no external evidence source still fits the append-only E slot.

Source: [`mdp.py`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/mdp.py).

## LLM-agent

*Expressiveness proof #5.* An LLM agent is a program that calls a language model in a loop, often with tools, to answer a question. Most engineers building with LLMs today build this, not Bayesian inference. The ontology fixes a closed set of hypotheses and the names of the tools the agent may call. Each step, the agent picks a tool, the tool returns evidence, and the LLM reports a new confidence vector across the hypotheses. R stays pure despite the LLM's non-determinism: every LLM response is recorded as an observation *before* R runs, and R only ever reads that recorded text — it never calls the LLM itself. Replay is deterministic conditioned on the recorded trace, the same conditional-determinism contract v1.0 already used.

Source: [`llm_agent.py`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/llm_agent.py).

## Worldview

*The one being shipped.* The other five encodings exist to demonstrate the tuple's reach. Worldview is the encoding the product is built on: a reader's evolving picture of a personal document corpus. O is the set of claim identifiers seen so far — it grows as documents introduce new claims. E is one LLM confidence vector per document, recording what that document said about which claims. B is a [Subjective Logic opinion](../beliefs/opinions.md) per claim, not a single number — an opinion separates *believed*, *disbelieved*, and *unknown* rather than collapsing them into one score.

R turns each new confidence vector into evidence, discounts it by source reliability, and accumulates it into every claim it mentions. Claims a document doesn't discuss are carried forward unchanged, so silence is never mistaken for disagreement.

!!! warning "Honest status"
    Source-reliability discounting is wired into R but fixed at 1.0 (a no-op) — the credibility weighting that would let unreliable sources count for less is not grounded yet.
    [Unit 3 of the worldview design spec](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md) tracks that work.

Source: [`worldview.py`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/worldview.py).

## Where next

- The math behind a worldview opinion: [Beliefs as numbers](../beliefs/index.md)
- How R stays pure across all six encodings: [The state tuple](state.md)
- The product built on the worldview encoding: [The worldview app](../worldview/index.md)
