import pytest
from promptdom.resolution.models import ResolutionCandidate
from promptdom.resolution.scorer import ScoringEngine

def test_scoring_engine_exact_match():
    scorer = ScoringEngine()
    candidate = ResolutionCandidate(target_type="button", text="Submit", selector="#submit")
    result = scorer.score("submit", "button", candidate)
    assert result.score >= 0.8
    assert "Exact Match" in result.match_reason

def test_scoring_engine_synonym_match():
    scorer = ScoringEngine()
    candidate = ResolutionCandidate(target_type="section", text="suggested videos", selector=".suggested")
    result = scorer.score("recommendations", "section", candidate)
    # recommendations has synonym "suggested". The candidate is "suggested videos", which contains "suggested" -> Partial Synonym
    assert result.score >= 0.5
    assert "Synonym Match" in result.match_reason

def test_scoring_engine_token_overlap():
    scorer = ScoringEngine()
    candidate = ResolutionCandidate(target_type="section", text="related channels list", selector=".channels")
    result = scorer.score("related videos", "section", candidate)
    assert result.score > 0
    assert "Token Overlap" in result.match_reason

def test_scoring_engine_text_penalty():
    scorer = ScoringEngine()
    c1 = ResolutionCandidate(target_type="button", text="Login", selector="#login1")
    c2 = ResolutionCandidate(target_type="button", text="Login and save your preferences", selector="#login2")
    
    r1 = scorer.score("login", "button", c1)
    r2 = scorer.score("login", "button", c2)
    
    assert r1.score > r2.score
