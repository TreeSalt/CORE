---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import re
import hashlib


@dataclass
class Hypothesis:
    """Represents a creative attack hypothesis with scoring and metadata"""
    id: str
    prompt_template: str
    score: float = 0.0
    confidence: float = 0.0
    risk_level: Optional[str] = None
    payload_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """LLM prompt template for hypothesis generation"""
    name: str
    description: str
    content: str
    parameters: List[str] = field(default_factory=list)
    version: str = "1.0"


class Scorer:
    """Multi-factor scoring system for hypothesis evaluation"""
    
    HEURISTICS = {
        'complexity': lambda h: h.metadata.get('complexity_score', 0),
        'novelty': lambda h: h.metadata.get('novelty_score', 0),
        'feasibility': lambda h: h.metadata.get('feasibility_score', 0),
        'impact': lambda h: h.metadata.get('impact_score', 0),
        'security_risk': lambda h: h.metadata.get('risk_score', 0),
    }
    
    def calculate(self, hypothesis: Hypothesis) -> float:
        """Calculate weighted composite score for hypothesis"""
        weights = {
            'complexity': 0.15,
            'novelty': 0.25,
            'feasibility': 0.30,
            'impact': 0.20,
            'security_risk': 0.10
        }
        
        score = sum(self.HEURISTICS[k](hypothesis) * weights.get(k, 0) 
                   for k in self.HEURISTICS.keys())
        
        # Apply confidence multiplier
        hypothesis.score = min(100, max(0, score * hypothesis.confidence))
        return hypothesis.score
    
    @staticmethod
    def normalize_score(score: float) -> float:
        """Normalize score to 0-1 range"""
        return min(1.0, max(0.0, score / 100.0))


class FalsePositiveFilter:
    """Filters out low-quality hypotheses that appear valid but aren't actionable"""
    
    COMMON_PATTERNS = [
        r'\b(please|could you|would you)\s+(please)?',  # Polite filler requests
        r'\bI\s+think\s+we\s+could\b',                 # Vague suggestion patterns
        r'\bas\s+a\s+general\b',                       # Generic responses
        r'\bjust\s+make\s+simpler',                    # Deflection attempts
    ]
    
    MIN_PAYLOAD_SCORE = 5.0
    MIN_CONFIDENCE_THRESHOLD = 0.7
    
    def filter(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """Filter out false positives from hypothesis list"""
        filtered = []
        
        for h in hypotheses:
            if self._check_confidence(h) and self._check_payload_score(h):
                if not self._detect_common_patterns(h):
                    filtered.append(h)
        
        return filtered
    
    def _check_confidence(self, hypothesis: Hypothesis) -> bool:
        """Check if hypothesis meets confidence threshold"""
        return hypothesis.confidence >= FalsePositiveFilter.MIN_CONFIDENCE_THRESHOLD
    
    def _check_payload_score(self, hypothesis: Hypothesis) -> bool:
        """Check if payload score exceeds minimum"""
        return Scorer.normalize_score(hypothesis.score) > FalsePositiveFilter.MIN_PAYLOAD_SCORE
    
    def _detect_common_patterns(self, hypothesis: Hypothesis) -> bool:
        """Detect and filter common false positive patterns"""
        content = hypothesis.metadata.get('content', '').lower()
        
        for pattern in COMMON_PATTERNS:
            if re.search(pattern, content):
                return True
        
        return False


class PayloadConverter:
    """Converts validated hypotheses into actionable payloads"""
    
    def convert(self, hypothesis: Hypothesis) -> Optional[Dict[str, Any]]:
        """Convert hypothesis to concrete payload format"""
        if not self._validate_hypothesis(hypothesis):
            return None
        
        payload = {
            'hypothesis_id': hypothesis.id,
            'prompt_template': hypothesis.prompt_template,
            'parameters': {k: v for k, v in hypothesis.metadata.items() 
                          if isinstance(v, (str, int, float))},
            'risk_level': hypothesis.risk_level or 'medium',
            'payload_type': hypothesis.payload_type,
            'signature': self._generate_signature(hypothesis),
            'validation_status': 'ready'
        }
        
        return payload
    
    def _validate_hypothesis(self, hypothesis: Hypothesis) -> bool:
        """Validate that hypothesis is ready for conversion"""
        return (hypothesis.score > 0 and 
                hypothesis.confidence > 0.5 and
                hypothesis.payload_type is not None)
    
    @staticmethod
    def _generate_signature(hypothesis: Hypothesis) -> str:
        """Generate unique signature for payload"""
        content = f"{hypothesis.id}:{hypothesis.score}:{hypothesis.confidence}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class PromptTemplates:
    """Repository of prompt templates for hypothesis generation"""
    
    TEMPLATES: Dict[str, PromptTemplate] = {}
    
    @staticmethod
    def register(name: str, template: PromptTemplate) -> None:
        """Register a new prompt template"""
        PromptTemplates.TEMPLATES[name] = template
    
    @classmethod
    def get_all(cls) -> List[PromptTemplate]:
        """Get all registered templates"""
        return list(cls.TEMPLATES.values())
    
    @classmethod
    def get_by_type(cls, payload_type: str) -> Optional[Dict[str, Any]]:
        """Get template by payload type"""
        for name, template in cls.TEMPLATES.items():
            if hasattr(template, 'payload_type') and template.payload_type == payload_type:
                return {'name': name, 'content': template.content}
        return None
    
    @staticmethod
    def create_complexity_analysis_template() -> PromptTemplate:
        """Create template for complexity-based attack analysis"""
        return PromptTemplate(
            name='complexity_analysis',
            description='Analyze prompt injection vectors through complexity lens',
            content="""You are analyzing a LLM's decision-making process. Your task is to identify:
1. Which intermediate reasoning steps could be influenced
2. Where complexity-based manipulation creates vulnerabilities
3. How depth-first vs breadth-first processing affects robustness

Consider these aspects when generating your analysis:
- Token count thresholds that trigger different behavior
- Chain-of-thought exposure opportunities
- Context window exploitation patterns""",
            parameters=['target_llm', 'context_window', 'token_budget'],
            payload_type='complexity'
        )
    
    @staticmethod
    def create_prompt_evolution_template() -> PromptTemplate:
        """Create template for prompt evolution tracking"""
        return PromptTemplate(
            name='prompt_evolution',
            description='Track how prompts evolve through interaction history',
            content="""Analyze the prompt injection attack vector by tracing:
1. Initial state → evolved state transformation path
2. How each user response modifies system behavior
3. Where adversarial input gains foothold
4. The amplification cascade mechanism

Key questions to answer:
- What changes occur in tokenization patterns?
- When does the model first deviate from baseline?
- Which guardrails prove ineffective at what threshold?""",
            parameters=['baseline_prompt', 'evolved_prompt', 'interaction_log'],
            payload_type='evolution'
        )
    
    @staticmethod
    def create_adversarial_benchmark_template() -> PromptTemplate:
        """Create template for adversarial benchmarking"""
        return PromptTemplate(
            name='adversarial_benchmark',
            description='Establish attack success metrics through benchmarking',
            content="""Construct adversarial benchmark suite to measure:
1. Success rate of different injection techniques
2. False positive vs true positive differentiation
3. Model-specific vulnerability fingerprints
4. Defense mechanism effectiveness

Benchmark categories:
- Semantic leakage detection
- Instruction override attempts
- Context contamination measurement
- Token smuggling success rates""",
            parameters=['model_version', 'test_suite', 'baseline_metrics'],
            payload_type='benchmark'
        )


class HypothesisGenerator:
    """Main generator for creative attack hypotheses"""
    
    def __init__(self):
        self.scorer = Scorer()
        self.filter = FalsePositiveFilter()
        self.converter = PayloadConverter()
        self.templates = PromptTemplates()
        
        # Register default templates
        self.templates.register('complexity_analysis', 
                              self.templates.create_complexity_analysis_template())
        self.templates.register('prompt_evolution', 
                              self.templates.create_prompt_evolution_template())
        self.templates.register('adversarial_benchmark', 
                              self.templates.create_adversarial_benchmark_template())
    
    def generate(self, target: Dict[str, Any], num_hypotheses: int = 10) -> List[Hypothesis]:
        """Generate creative attack hypotheses for given target"""
        hypotheses = []
        
        templates = self.templates.get_all()
        
        for i, template in enumerate(templates):
            # Generate hypothesis variations based on target analysis
            base_score = self._assess_initial_vulnerability(target)
            base_confidence = self._calculate_initial_confidence(target)
            
            for j in range(num_hypotheses // len(templates)):
                hypothesis = Hypothesis(
                    id=f"{template.name}_{i}-{j}",
                    prompt_template=template.content,
                    score=base_score + (j * 2),
                    confidence=min(0.99, base_confidence + (j * 0.05)),
                    risk_level=self._determine_risk_level(base_score),
                    payload_type=template.payload_type,
                    metadata={
                        'target_info': target.get('id', ''),
                        'complexity_score': self._score_complexity(target),
                        'novelty_score': self._score_novelty(template),
                        'feasibility_score': self._score_feasibility(target, template),
                        'impact_score': self._score_impact(target, template),
                        'risk_score': base_score * 0.5
                    }
                )
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _assess_initial_vulnerability(self, target: Dict[str, Any]) -> float:
        """Assess initial vulnerability level of target"""
        # Simplified vulnerability assessment
        vulnerabilities = {
            'llm_type': 0.1,
            'context_length': 0.15,
            'model_temperature': 0.12,
            'system_instructions': 0.18,
            'default_behavior': 0.14,
            'training_data_quality': 0.15,
            'knowledge_cutoff': 0.16
        }
        
        score = 0
        for key in vulnerabilities:
            score += getattr(target, key, 0) * vulnerabilities[key]
        
        return min(95.0, max(0, score))
    
    def _calculate_initial_confidence(self, target: Dict[str, Any]) -> float:
        """Calculate initial confidence level"""
        base = 0.6
        adjustments = {
            'model_size': 0.1,
            'security_layer': -0.2,
            'prompt_complexity': 0.05
        }
        
        score = base
        for key in adjustments:
            val = getattr(target, key, None)
            if val is not None:
                score += adjustments[key] * val
        
        return min(0.99, max(0.1, score))
    
    def _determine_risk_level(self, base_score: float) -> str:
        """Determine risk level based on score"""
        if base_score < 25:
            return 'low'
        elif base_score < 50:
            return 'medium'
        elif base_score < 75:
            return 'high'
        else:
            return 'critical'
    
    def _score_complexity(self, target: Dict[str, Any]) -> float:
        """Score complexity of attack vector"""
        return min(100, max(0, len(str(target.get('prompt', '')))) * 0.5)
    
    def _score_novelty(self, template: PromptTemplate) -> float:
        """Score novelty of prompt approach"""
        content = template.content.lower()
        novel_terms = ['injection', 'evolutionary', 'adversarial']
        score = len(set(novel_terms) & set(content)) * 20
        return min(100, max(0, score + 30))
    
    def _score_feasibility(self, target: Dict[str, Any], template: PromptTemplate) -> float:
        """Score feasibility of attack execution"""
        base = 70
        penalties = {
            'requires_network': 25,
            'local_only': -15,
            'api_access': -5
        }
        
        score = base
        if target.get('network_accessible'):
            score += penalties.get('requires_network', 0)
        if target.get('is_local'):
            score += penalties.get('local_only', 0)
        
        return min(100, max(0, score))
    
    def _score_impact(self, target: Dict[str, Any], template: PromptTemplate) -> float:
        """Score potential impact of successful attack"""
        impact_factors = {
            'data_exfiltration': 40,
            'prompt_injection': 35,
            'instruction_override': 25,
            'system_hallucination': 15
        }
        
        score = 0
        for factor, weight in impact_factors.items():
            if template.content.lower().find(factor) != -1:
                score += weight
        
        return min(100, max(0, score))


def run_specter_analysis(target: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
    """Run complete SPECTER creative analysis layer on target"""
    generator = HypothesisGenerator()
    
    # Generate hypotheses
    all_hypotheses = generator.generate(target, num_hypotheses=20)
    
    # Score and filter
    for h in all_hypotheses:
        Scorer().calculate(h)
    
    filtered = FalsePositiveFilter().filter(all_hypotheses)
    
    # Convert top hypotheses to payloads
    payloads = []
    for h in sorted(filtered, key=lambda x: x.score, reverse=True)[:top_k]:
        payload = generator.converter.convert(h)
        if payload:
            payloads.append(payload)
    
    return payloads
```