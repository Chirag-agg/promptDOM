from .models import ResolutionCandidate

class ScoringEngine:
    SYNONYM_MAP = {
        "recommendations": ["recommended", "suggested", "related", "recommended videos"],
        "comments": ["discussion", "replies"],
        "sidebar": ["side panel", "secondary", "aside"]
    }

    def score(self, target: str, target_type: str, candidate: ResolutionCandidate) -> ResolutionCandidate:
        t_lower = target.lower().strip()
        c_lower = candidate.text.lower().strip()
        c_type = candidate.target_type
        
        # Base score
        score = 0.0
        match_reason = "No significant match"
        
        # 1. Exact Match
        if t_lower == c_lower:
            score += 0.8
            match_reason = "Exact Match"
        else:
            # 2. Synonym / Partial Match
            synonyms = self._get_synonyms(t_lower)
            matched_synonym = False
            for syn in synonyms:
                if syn == c_lower:
                    score += 0.75
                    match_reason = f"Exact Synonym Match ({syn})"
                    matched_synonym = True
                    break
                elif syn in c_lower:
                    score += 0.5
                    match_reason = f"Partial Synonym Match ({syn})"
                    matched_synonym = True
                    break
            
            if not matched_synonym:
                if t_lower in c_lower:
                    score += 0.5
                    match_reason = "Partial Match"
                else:
                    # 3. Token Overlap
                    t_tokens = set(t_lower.split())
                    c_tokens = set(c_lower.split())
                    if t_tokens and c_tokens:
                        overlap = t_tokens.intersection(c_tokens)
                        if overlap:
                            overlap_ratio = len(overlap) / len(t_tokens)
                            score += overlap_ratio * 0.4
                            match_reason = f"Token Overlap ({', '.join(overlap)})"
        
        # If no base score, don't bother with modifiers
        if score > 0:
            # 4. Type Match
            if target_type != "unknown" and target_type == c_type:
                score += 0.15
                
            # 5. Text Length Penalty
            length_diff = max(0, len(c_lower) - len(t_lower))
            penalty = min(0.3, length_diff * 0.01)
            score -= penalty
            
        candidate.score = max(0.0, min(1.0, score))
        candidate.match_reason = match_reason
        return candidate

    def _get_synonyms(self, target: str) -> list[str]:
        synonyms = []
        for key, values in self.SYNONYM_MAP.items():
            if target == key:
                synonyms.extend(values)
            elif target in values:
                synonyms.append(key)
                synonyms.extend([v for v in values if v != target])
        return synonyms
