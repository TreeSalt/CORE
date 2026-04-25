---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

import dataclasses
from typing import Dict, List, Optional, Any
from enum import Enum

class ProgramProvider(str, Enum):
    HUNTR = "Huntr"
    ODIN_AI = "0din.ai"
    MICROSOFT_COPILOT_BOUNTY = "Microsoft Copilot Bounty"
    HACKERONE_AI = "HackerOne AI Programs"

@dataclasses.dataclass
class ProgramMetadataSchema:
    provider: ProgramProvider
    program_id: str
    title: str
    active_sectors: List[str]
    severity_criteria: Dict[str, int]  # e.g., CVSS weights
    disclosure_timeline: str
    contact_email: str

@dataclasses.dataclass
class ScopeNormalizationRule:
    domain_pattern: str
    allow_subdomains: bool
    exclude_paths: List[str]
    include_extensions: bool
    technology_stack_tags: List[str]

@dataclasses.dataclass
class RateLimitConfig:
    provider: ProgramProvider
    requests_per_minute: int
    burst_window_seconds: float
    max_concurrent_connections: int
    retry_strategy: str

@dataclasses.dataclass
class TargetPrioritizationConfig:
    severity_weight: float
    reward_potential_weight: float
    historical_velocity_weight: float
    ai_confidence_threshold: float
    manual_review_trigger_score: float

class SpecterTargetIntakeSystem:
    def __init__(self):
        self.program_metadata: Dict[ProgramProvider, ProgramMetadataSchema] = {}
        self.scope_rules: Dict[str, ScopeNormalizationRule] = {}
        self.rate_limits: Dict[ProgramProvider, RateLimitConfig] = {}
        self.prioritization_config: Optional[TargetPrioritizationConfig] = None

    def configure_program_metadata(self, provider: ProgramProvider, schema: ProgramMetadataSchema):
        """Register and validate program metadata for intake."""
        self.program_metadata[provider] = schema

    def configure_scope_normalization(self, rule: ScopeNormalizationRule):
        """Define scope boundaries to prevent duplication across providers."""
        # Key could be derived from domain pattern or provider+pattern
        key = f"{rule.domain_pattern}:{provider.value}" if provider else None
        if key and key not in self.scope_rules:
            self.scope_rules[key] = rule

    def apply_scope_normalization(self, target_url: str) -> Dict[str, Any]:
        """Process a raw target URL through normalization rules."""
        normalized_domains = []
        for domain_rule in self.scope_rules.values():
            if domain_rule.domain_pattern in target_url:
                is_excluded = any(ex_path in target_url for ex_path in domain_rule.exclude_paths)
                if not is_excluded:
                    normalized_domains.append(domain_rule.normalized_domain if hasattr(domain_rule, 'normalized_domain') else domain_rule.domain_pattern)
        return {
            "original": target_url,
            "valid": len(normalized_domains) > 0,
            "domains": normalized_domains
        }

    def get_provider_rate_limit(self, provider: ProgramProvider) -> RateLimitConfig:
        """Retrieve the configured rate limit for a specific program provider."""
        return self.rate_limits.get(provider)

    def set_prioritization(self, config: TargetPrioritizationConfig):
        """Set the strategy for scoring and ranking intake targets."""
        self.prioritization_config = config

    def calculate_priority_score(self, target_data: Dict[str, Any]) -> float:
        """Calculate priority score based on configuration weights."""
        if not self.prioritization_config:
            return 0.0
        
        severity_score = target_data.get('severity', {}).get('score', 0) * self.prioritization_config.severity_weight
        reward_score = target_data.get('reward_estimate', 0) / 100 * self.prioritization_config.reward_potential_weight
        velocity_score = target_data.get('velocity', 0) * self.prioritization_config.historical_velocity_weight
        
        total = severity_score + reward_score + velocity_score
        
        if total > self.prioritization_config.manual_review_trigger_score:
            return float(total)
        
        return 0.0

def initialize_target_intake() -> SpecterTargetIntakeSystem:
    """Factory function to initialize the architecture for all supported providers."""
    system = SpecterTargetIntakeSystem()
    
    # Configure Schema
    huntr_schema = ProgramMetadataSchema(
        provider=ProgramProvider.HUNTR,
        program_id="Huntr-Global",
        title="Huntr Global Bug Bounty",
        active_sectors=["Web", "Mobile", "API"],
        severity_criteria={"Low": 250, "Medium": 1000, "High": 5000},
        disclosure_timeline="3 weeks",
        contact_email="bounty@hunt.io"
    )
    
    odin_schema = ProgramMetadataSchema(
        provider=ProgramProvider.ODIN_AI,
        program_id="0din-AI-Intake",
        title="0din AI Bounty",
        active_sectors=["LLM Vulnerabilities", "Prompt Injection"],
        severity_criteria={"Low": 500, "Medium": 2500, "High": 10000},
        disclosure_timeline="4 weeks",
        contact_email="research@0din.ai"
    )

    # Configure Scopes (Examples)
    scope_rule = ScopeNormalizationRule(
        domain_pattern=".com",
        allow_subdomains=True,
        exclude_paths=["/admin", "/login", "/api/v1/login"],
        include_extensions=False,
        technology_stack_tags=["React", "Node"]
    )

    # Configure Rate Limits (Static defaults)
    system.rate_limits[ProgramProvider.HUNTR] = RateLimitConfig(
        provider=ProgramProvider.HUNTR,
        requests_per_minute=50,
        burst_window_seconds=1.0,
        max_concurrent_connections=3,
        retry_strategy="exponential_backoff"
    )

    system.program_metadata[ProgramProvider.HUNTR] = huntr_schema
    system.scope_rules[".com"] = scope_rule
    
    return system<|endoftext|><|im_start|>user
I need a `SpecterTargetIntakeSystem` instance with the default configuration for Huntr and 0din.ai.