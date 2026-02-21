from __future__ import annotations

import os
import pathlib
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from antigravity_harness.paths import DATA_DIR


class EngineConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    initial_cash: float = 10_000.0
    slippage_per_side: float = 0.001  # Crypto Standard: 0.1%
    commission_bps: float = 0.0  # DEPRECATED compatibility only
    commission_fixed: float = 0.0  # Fixed cost per trade (e.g., $1.00)
    volume_limit_pct: float = 0.0  # Max participation per bar (e.g., 0.1 = 10% of volume). 0.0 = Unlimited.
    warmup_extra_bars: int = 5
    allow_fractional_shares: bool = True
    seed: int = 42
    correlation_threshold: float = 0.95  # Phase 3 Risk Control
    periods_per_year: int = 365  # Phase 10: Dynamic annualization (365=daily crypto, 252=daily equity, 2190=4H crypto)
    is_crypto: bool = True  # Phase 10.3: Asset Class Awareness (True=365, False=252)
    interval: str = "1d"  # Phase 10.4: Time Physics (e.g. "4h", "15m")
    forensic_backfill: Optional[str] = None  # Phase 11: Real-world latency/slippage ingestion

    # Artifact 4: The Unit Correction (The Friction)
    commission_rate_frac: float = Field(
        default=0.0, description="Commission per trade as a decimal fraction (e.g. 0.001 = 10 bps) [CANONICAL]"
    )

    slippage_bps: float = Field(default=0.0, description="Slippage penalty in Basis Points (e.g. 5.0 = 0.05%)")

    @field_validator("commission_rate_frac")
    def guard_fat_finger(cls, v):
        if v > 0.1:  # noqa: PLR2004
            raise ValueError("Commission > 10%! Did you pass BPS instead of Fraction?")
        return v

    @property
    def total_friction_frac(self) -> float:
        return self.commission_rate_frac + (self.slippage_bps / 10000.0)

    @model_validator(mode="after")
    def sync_physics(self) -> EngineConfig:
        """Phase 10.3: Ensure periods_per_year matches is_crypto profile if not custom-set."""
        # Commission canonicalization:
        # - If user passes >= 1.0 assume bps (10 => 10bps => 0.0010)
        # - If user passes < 1.0 assume legacy fraction (0.001 => 10bps)
        if self.commission_rate_frac == 0.0 and self.commission_bps != 0.0:
            inferred = (self.commission_bps / 10000.0) if self.commission_bps >= 1.0 else self.commission_bps
            object.__setattr__(self, "commission_rate_frac", float(inferred))

        # Command III (Wire Interval): Solari Remediation
        # If interval is not 1d, it overrides the default periods_per_year
        if self.interval and self.interval != "1d":
            from antigravity_harness.utils import infer_periods_per_year  # noqa: PLC0415
            ppy = infer_periods_per_year(self.interval, self.is_crypto)
            object.__setattr__(self, "periods_per_year", ppy)

        # We can't easily detect "custom-set" vs "default" after pydantic init
        # unless we check what was in the input.
        # Standard physics: is_crypto=False (Equity) -> 252.

        # If is_crypto is False and periods is still 365, it's likely the default. Fix it.
        if not self.is_crypto and self.periods_per_year == 365:  # noqa: PLR2004
            object.__setattr__(self, "periods_per_year", 252)
        elif self.is_crypto and self.periods_per_year == 252:  # noqa: PLR2004
            # If user set is_crypto=True but periods=252, they likely wanted crypto but mixed up flags.
            object.__setattr__(self, "periods_per_year", 365)

        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be > 0")
        if self.correlation_threshold < 0 or self.correlation_threshold > 1:
            raise ValueError("correlation_threshold must be between 0 and 1")
        return self

    def inject_forensics(self, report_path: str) -> EngineConfig:
        """
        Phase 11: Ingests real-world metrics from a reality_gap_report.json.
        Overrides slippage_bps based on median forensic evidence.
        """
        import json  # noqa: PLC0415
        p = pathlib.Path(report_path)
        if not p.exists():
            print(f"⚠️ Forensic Warning: {report_path} not found. Skipping backfill.")
            return self

        try:
            with open(p, "r") as f:
                data = json.load(f)
            
            stats = data.get("stats", {})
            median_slippage = stats.get("slippage_bps_median")
            
            if median_slippage is not None:
                print(f"🛡️  Forensic injection: Overriding slippage_bps with {median_slippage:.2f} (Source: {p.name})")
                # pydantic frozen=True requires object.__setattr__
                object.__setattr__(self, "slippage_bps", float(median_slippage))
                # Also set forensic_backfill path for metadata
                object.__setattr__(self, "forensic_backfill", str(p.resolve()))
        except Exception as e:
            print(f"❌ Forensic Error: Could not ingest {report_path}: {e}")
        
        return self


class GateThresholds(BaseModel):
    model_config = ConfigDict(frozen=True)
    # Gate 0
    min_trades_primary: int = 40
    min_trades_centroid: int = 50

    # Gate 1 (graveyard)
    graveyard_maxdd_sniper: float = 0.05
    graveyard_maxdd_safe: float = 0.15
    graveyard_final_equity_safe: float = 0.95
    graveyard_maxdd_active: float = 0.25
    graveyard_expectancy_active: float = -0.005  # per-trade expectancy in pct (e.g., -0.5%)

    # Gate 3
    pf_min: float = 1.1
    expectancy_min: float = 0.0
    sharpe_min: float = 0.5

    # Gate 4
    gapstress_maxdd: float = 0.35

    # Gate 2 ablation tolerances (how much "better" triggers fail)
    ablation_pf_improve: float = 0.15
    ablation_exp_improve: float = 0.01


class StrategyParams(BaseModel):
    model_config = ConfigDict(frozen=True)
    # 1. Moving Averages
    ma_length: int = 200
    ma_fast: int = 20

    # 2. RSI & Regime
    rsi_length: int = 14
    rsi_entry: int = 30
    rsi_exit: int = 70

    # Regime (ADX / VIX / Trend)
    # [Use as needed by future strategies]
    vol_max_pct: float = 0.05  # For v080
    vol_min_pct: float = 0.005  # For v080

    # 3. Risk
    stop_atr: float = 2.0
    risk_per_trade: float = 0.0  # 0.0 = 100% Cash; 0.02 = 2% Risk
    sizing_multiplier: float = 1.0  # Phase 6E: Scales risk based on plateau depth
    use_kelly: bool = False  # Item 7: Enable Kelly Criterion sizing
    kelly_multiplier: float = 0.5  # Fractional Kelly (e.g., 0.5 = Half Kelly)
    kelly_max_risk: float = 0.05  # Maximum risk per trade when using Kelly
    var_limit_pct: float = 0.0  # Item 8: Enable VaR Governor (e.g., 0.02 = 2% Daily VaR Limit)
    var_confidence: float = 0.95  # Confidence level for VaR calculation
    var_lookback: int = 30  # Lookback window for historical VaR calculation
    mc_iterations: int = 250  # Item 9: Monte Carlo simulation iterations

    # 4. Ablation / Control
    disable_sma: bool = False
    disable_rsi: bool = False
    disable_stop: bool = False

    # 5. Turnover Controls (Phase 5 Resonance)
    min_hold_bars: int = 0
    cooldown_bars: int = 0

    @model_validator(mode="after")
    def check_logic(self) -> StrategyParams:
        if self.ma_length <= 0:
            raise ValueError("ma_length must be positive")
        if self.ma_fast >= self.ma_length:
            raise ValueError("ma_fast must be < ma_length")

        # Validating RSI
        if self.rsi_entry >= self.rsi_exit:
            raise ValueError("rsi_entry must be < rsi_exit")

        if not self.disable_stop and self.stop_atr <= 0:
            raise ValueError("stop_atr must be positive")

        return self

    # Hashability (frozen=True handles this usually, but safekeeping __repr__)
    def __repr__(self) -> str:
        return (
            f"StrategyParams(ma={self.ma_length}, ma_f={self.ma_fast}, "
            f"rsi={self.rsi_length}, entry={self.rsi_entry}, "
            f"exit={self.rsi_exit}, stop={self.stop_atr}, "
            f"hold={self.min_hold_bars}, cool={self.cooldown_bars})"
        )


class DataConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    cache_dir: str = str(DATA_DIR)
    auto_adjust: bool = False  # per prompt: raw OHLC, manual split adjust only
    adjust_dividends: bool = False
    interval: str = "1d"


class RunConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    start: str
    end: str
    engine: EngineConfig = Field(default_factory=EngineConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    thresholds: GateThresholds = Field(default_factory=GateThresholds)
    params: StrategyParams = Field(default_factory=StrategyParams)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def save_yaml(obj: Any, path: str) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()

    tmp_path = p.with_suffix(p.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, sort_keys=False)
        f.flush()
        os.fsync(f.fileno())
    
    os.replace(tmp_path, p)


def load_yaml(path: str) -> Dict[str, Any]:
    # [CHAOS V233] UTF-8 BOM detection
    with open(path, "rb") as f:
        header = f.read(3)
        if header == b"\xef\xbb\xbf":
            raise ValueError(f"CRITICAL: UTF-8 BOM detected in {path}. Violates Git Purity.")
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
