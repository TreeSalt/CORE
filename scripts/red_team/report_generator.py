import json
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path
from datetime import datetime

@dataclass
class ProbeResult:
    category: str
    name: str
    status: str
    score: float
    response: str

@dataclass
class CampaignResults:
    timestamp: datetime
    model: str
    probes: List[ProbeResult]

@dataclass
class Anomaly:
    name: str
    score: float
    response_preview: str

def load_results(results_path: Path) -> CampaignResults:
    with open(results_path, 'r') as file:
        data = json.load(file)
    timestamp = datetime.fromisoformat(data['timestamp'])
    model = data['model']
    probes = [ProbeResult(**probe) for probe in data['probes']]
    return CampaignResults(timestamp, model, probes)

def generate_executive_summary(campaign: CampaignResults) -> str:
    total_probes = len(campaign.probes)
    anomalies = [probe for probe in campaign.probes if probe.score > 0]
    anomaly_rate = len(anomalies) / total_probes * 100 if total_probes > 0 else 0
    return (
        f"## Executive Summary\n"
        f"- **Timestamp:** {campaign.timestamp}\n"
        f"- **Model Tested:** {campaign.model}\n"
        f"- **Total Probes:** {total_probes}\n"
        f"- **Anomaly Rate:** {anomaly_rate:.2f}%\n"
    )

def generate_findings_section(probes: List[ProbeResult]) -> str:
    findings = {}
    for probe in probes:
        findings.setdefault(probe.category, []).append(probe)
    findings_section = "## Findings\n"
    for category, probes in findings.items():
        findings_section += f"### {category}\n"
        for probe in probes:
            findings_section += f"- **{probe.name}:** {probe.status}\n"
    return findings_section

def generate_top_anomalies_section(probes: List[ProbeResult]) -> str:
    anomalies = sorted([probe for probe in probes if probe.score > 0], key=lambda x: x.score, reverse=True)[:10]
    top_anomalies_section = "## Top Anomalies\n"
    for anomaly in anomalies:
        response_preview = anomaly.response[:100] + "..." if len(anomaly.response) > 100 else anomaly.response
        top_anomalies_section += f"- **{anomaly.name}:** Score: {anomaly.score:.2f}, Response Preview: {response_preview}\n"
    return top_anomalies_section

def generate_methodology_section() -> str:
    return (
        "## Methodology\n"
        "The red team conducted a series of probes to evaluate the security posture of the target system. "
        "Probes were categorized and executed to assess different aspects of the system's security. "
        "Anomalies were identified based on the response scores from each probe."
    )

def generate_raw_data_section(probes: List[ProbeResult]) -> str:
    raw_data_section = "## Raw Data\n"
    for probe in probes:
        raw_data_section += f"- **Name:** {probe.name}, **Category:** {probe.category}, **Status:** {probe.status}, **Score:** {probe.score:.2f}, **Response:** {probe.response}\n"
    return raw_data_section

def generate_report(results_path: Path, output_path: Path) -> None:
    campaign = load_results(results_path)
    report = (
        generate_executive_summary(campaign) +
        generate_findings_section(campaign.probes) +
        generate_top_anomalies_section(campaign.probes) +
        generate_methodology_section() +
        generate_raw_data_section(campaign.probes)
    )
    output_path.write_text(report)

# Example usage:
# generate_report(Path('path/to/probe_results.json'), Path('path/to/output_report.md'))
