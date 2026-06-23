"""Subjective Logic: binomial opinions as evidence counts.

An ``Opinion`` is a belief about one binary claim, stored as the evidence
counts ``(r, s)`` that produced it plus a base rate. The Subjective-Logic
view (belief ``b``, disbelief ``d``, uncertainty ``u``) is derived, not
stored. With non-informative prior weight ``W = 2``:

    b = r / (r + s + W)
    d = s / (r + s + W)
    u = W / (r + s + W)
    P = b + base_rate * u      # projected probability

Storing counts instead of ``(b, d, u)`` makes the update both trivial and
robust: cumulative fusion is just count addition, which is associative
and order-independent, so the division-by-zero corner cases of the
pairwise ``(b, d, u)`` fusion formulas never arise. This is the
correction the design's gate condition asks for, obtained by
construction rather than by patching the pairwise forms.

The opinion-to-Beta mapping (an Opinion's counts are the
``Beta(r + 1, s + 1)`` pseudo-counts) is treated here as a
*parameterization* whose worth is judged by calibration downstream, not
as a proven isomorphism of belief. ``W = 2`` is the binary-frame
convention; each claim is its own independent binomial, so the
convention stays exact.

This module is pure math. How an LLM confidence becomes evidence counts
is the worldview encoding's job, not this module's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# Non-informative prior weight. 2 gives a uniform prior on a binary frame.
W = 2.0


@dataclass(frozen=True)
class Opinion:
    """A binomial Subjective-Logic opinion, stored as evidence counts.

    r: weighted evidence FOR the claim (supporting pseudo-count) >= 0.
    s: weighted evidence AGAINST the claim (disconfirming pseudo-count) >= 0.
    base_rate: prior probability before any evidence, in [0, 1].

    A vacuous opinion ``Opinion(0, 0)`` has uncertainty 1 and projects to
    its base rate: it represents "I have no evidence", which a single
    probability cannot say.
    """

    r: float
    s: float
    base_rate: float = 0.5

    def __post_init__(self) -> None:
        """Reject negative counts or an out-of-range base rate."""
        if self.r < 0 or self.s < 0:
            msg = f"counts must be >= 0, got r={self.r}, s={self.s}"
            raise ValueError(msg)
        if not 0.0 <= self.base_rate <= 1.0:
            msg = f"base_rate must be in [0, 1], got {self.base_rate}"
            raise ValueError(msg)

    @property
    def belief(self) -> float:
        """Belief mass b = r / (r + s + W)."""
        return self.r / (self.r + self.s + W)

    @property
    def disbelief(self) -> float:
        """Disbelief mass d = s / (r + s + W)."""
        return self.s / (self.r + self.s + W)

    @property
    def uncertainty(self) -> float:
        """Uncertainty mass u = W / (r + s + W). 1.0 when there is no evidence."""
        return W / (self.r + self.s + W)

    @property
    def projected(self) -> float:
        """Projected probability P = b + base_rate * u."""
        return self.belief + self.base_rate * self.uncertainty


def _check_nonempty(opinions: Sequence[Opinion]) -> None:
    if not opinions:
        msg = "cannot fuse an empty sequence of opinions"
        raise ValueError(msg)


def fuse_cumulative(opinions: Sequence[Opinion]) -> Opinion:
    """Fuse independent opinions by accumulating evidence (count addition).

    Cumulative fusion is the right operator when sources are independent:
    more independent evidence lowers uncertainty. Because it is plain
    count addition, it is associative and order-independent, so fusing a
    list gives the same result in any order.

    Beware: with many sources this drives uncertainty toward 0, so it
    manufactures false confidence from duplicates. Use
    ``fuse_averaging`` when independence is unproven.

    Args:
        opinions: one or more opinions about the *same* claim (they share
            a base rate; the first operand's base rate is kept).

    Returns:
        The accumulated opinion.

    Raises:
        ValueError: if ``opinions`` is empty.
    """
    _check_nonempty(opinions)
    return Opinion(
        r=sum(o.r for o in opinions),
        s=sum(o.s for o in opinions),
        base_rate=opinions[0].base_rate,
    )


def fuse_averaging(opinions: Sequence[Opinion]) -> Opinion:
    """Fuse dependent opinions by averaging evidence counts.

    Averaging fusion is the right operator when sources are *not*
    independent (duplicates, retweets, shared upstream): N copies of one
    claim count as one, so uncertainty does not collapse. This is the
    defense against a manufactured-consensus "meme farm".

    Args:
        opinions: one or more opinions about the same claim.

    Returns:
        The averaged opinion.

    Raises:
        ValueError: if ``opinions`` is empty.
    """
    _check_nonempty(opinions)
    n = len(opinions)
    return Opinion(
        r=sum(o.r for o in opinions) / n,
        s=sum(o.s for o in opinions) / n,
        base_rate=opinions[0].base_rate,
    )


def discount(opinion: Opinion, reliability: float) -> Opinion:
    """Scale an opinion's evidence by a source's reliability in [0, 1].

    Discounting is how source credibility enters: a document's evidence
    is scaled by how much the source is trusted. The lost evidence
    becomes uncertainty, not false confidence -- at reliability 0 the
    opinion goes fully vacuous (the source is ignored), at reliability 1
    it is unchanged.

    Args:
        opinion: the evidence a source contributes.
        reliability: the source's trust factor P_R in [0, 1].

    Returns:
        The discounted opinion.

    Raises:
        ValueError: if ``reliability`` is outside [0, 1].
    """
    if not 0.0 <= reliability <= 1.0:
        msg = f"reliability must be in [0, 1], got {reliability}"
        raise ValueError(msg)
    return Opinion(
        r=opinion.r * reliability,
        s=opinion.s * reliability,
        base_rate=opinion.base_rate,
    )
