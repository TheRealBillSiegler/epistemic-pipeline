"""Tests for the Subjective Logic math module (SL Unit 1, #17)."""

import math

import pytest

from epistemic_pipeline.encodings._subjective_logic import (
    Opinion,
    discount,
    fuse_averaging,
    fuse_cumulative,
)


class TestOpinion:
    def test_vacuous_is_total_uncertainty(self):
        op = Opinion(0, 0)
        assert op.belief == 0.0
        assert op.disbelief == 0.0
        assert op.uncertainty == 1.0
        assert op.projected == 0.5  # base_rate

    def test_vacuous_projects_to_base_rate(self):
        assert Opinion(0, 0, base_rate=0.2).projected == pytest.approx(0.2)

    @pytest.mark.parametrize(
        ("r", "s"),
        [(0, 0), (1, 0), (0, 1), (3, 2), (10, 0), (0.5, 0.5)],
    )
    def test_masses_sum_to_one(self, r, s):
        op = Opinion(r, s)
        assert op.belief + op.disbelief + op.uncertainty == pytest.approx(1.0)

    def test_more_evidence_lowers_uncertainty(self):
        assert Opinion(10, 0).uncertainty < Opinion(1, 0).uncertainty

    def test_projected_formula(self):
        op = Opinion(3, 1, base_rate=0.5)
        # b = 3/6 = 0.5, u = 2/6, P = 0.5 + 0.5*(2/6)
        assert op.projected == pytest.approx(0.5 + 0.5 * (2 / 6))

    def test_negative_count_rejected(self):
        with pytest.raises(ValueError, match="counts must be >= 0"):
            Opinion(-1, 0)

    def test_base_rate_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="base_rate"):
            Opinion(1, 1, base_rate=1.5)


class TestCumulativeFusion:
    def test_adds_counts(self):
        fused = fuse_cumulative([Opinion(2, 1), Opinion(3, 0)])
        assert fused.r == 5
        assert fused.s == 1

    def test_order_independent(self):
        ops = [Opinion(1, 0), Opinion(0, 2), Opinion(3, 1), Opinion(2, 2)]
        forward = fuse_cumulative(ops)
        backward = fuse_cumulative(list(reversed(ops)))
        assert forward == backward

    def test_collapses_uncertainty_with_repetition(self):
        one = Opinion(2, 0)
        many = fuse_cumulative([one] * 5)
        assert many.uncertainty < one.uncertainty

    def test_single_opinion_unchanged(self):
        op = Opinion(2, 3)
        assert fuse_cumulative([op]) == op

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            fuse_cumulative([])


class TestAveragingFusion:
    def test_duplicates_do_not_collapse_uncertainty(self):
        # The meme-farm guard: N copies of one claim count as one.
        one = Opinion(2, 0)
        averaged = fuse_averaging([one] * 10)
        assert averaged.uncertainty == pytest.approx(one.uncertainty)
        assert averaged == one

    def test_averages_distinct_counts(self):
        avg = fuse_averaging([Opinion(4, 0), Opinion(0, 2)])
        assert avg.r == pytest.approx(2.0)
        assert avg.s == pytest.approx(1.0)

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            fuse_averaging([])


class TestDiscount:
    def test_zero_reliability_is_vacuous(self):
        d = discount(Opinion(5, 3), 0.0)
        assert d.uncertainty == 1.0
        assert d.r == 0.0
        assert d.s == 0.0

    def test_full_reliability_unchanged(self):
        op = Opinion(5, 3)
        assert discount(op, 1.0) == op

    def test_partial_reliability_raises_uncertainty(self):
        op = Opinion(4, 4)
        half = discount(op, 0.5)
        assert half.r == pytest.approx(2.0)
        assert half.s == pytest.approx(2.0)
        assert half.uncertainty > op.uncertainty

    @pytest.mark.parametrize("bad", [-0.1, 1.5])
    def test_reliability_out_of_range_rejected(self, bad):
        with pytest.raises(ValueError, match="reliability"):
            discount(Opinion(1, 1), bad)


def test_meme_farm_scenario():
    """Cumulative collapses under duplicates; averaging holds the line."""
    meme = Opinion(1, 0)  # one low-credibility claim
    farm = [meme] * 50
    assert fuse_cumulative(farm).uncertainty < 0.05  # manufactured confidence
    assert fuse_averaging(farm).uncertainty == pytest.approx(meme.uncertainty)


def test_discount_then_fuse_is_the_update_shape():
    """A low-credibility source barely moves belief; high-credibility moves it."""
    claim = Opinion(2, 0)
    prior = Opinion(0, 0)
    weak = fuse_cumulative([prior, discount(claim, 0.02)])
    strong = fuse_cumulative([prior, discount(claim, 0.95)])
    assert weak.belief < 0.05
    assert strong.belief > weak.belief
    assert weak.uncertainty > strong.uncertainty
    assert not math.isnan(weak.projected)
