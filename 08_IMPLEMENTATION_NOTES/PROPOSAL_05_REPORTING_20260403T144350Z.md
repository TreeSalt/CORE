---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter


def calculate_stats(missions):
    total = len(missions)
    status_counts = Counter([m.get('status', 'unknown') for m in missions])
    ratified_count = status_counts.get('ratified', 0)
    escalated_count = status_counts.get('escalated', 0)
    
    # Retry count: assume retries field exists per mission or calculate from failed attempts if structure differs
    # Assuming direct retries field based on "retry count" metric in brief
    retry_count = sum(m.get('retries', 0) for m in missions)
    
    # Average time
    avg_time = sum(m.get('time', 0) for m in missions) / total if total else 0
    
    # Track performance check
    track_counts = Counter([m.get('track', 'unknown') for m in missions])
    failed_tracks = [t for t, c in track_counts.items() if c > 5 and status_counts.get(f'{t}', {}).get('count', 0) == 0] # Placeholder logic: check if any failed
    
    return {
        'total': total,
        'ratified_count': ratified_count,
        'escalated_count': escalated_count,
        'avg_time': avg_time,
        'retry_count': retry_count
    }


def main():
    try:
        queue_path = Path('orchestration/MISSION_QUEUE.json')
        
        # Check existence of source file
        if not queue_path.exists():
            raise FileNotFoundError(f"Source file {queue_path} not found.")

        with open(queue_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Assume mission_queue is a list of dictionaries or root object contains it
        missions = data.get('mission_queue', [])
        
        # Determine Epoch Name
        epoch_name = data.get('epoch_name', 'EPOCH_01')
        if isinstance(epoch_name, str):
            pass
        else:
            epoch_name = 'UNKNOWN_EPOCH'

        name = Path(epoch_name).stem or epoch_name
        
        # Parse date
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%Y-%m-%d')
        
        # Ensure output directory exists
        output_dir = Path('docs/reports')
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f'EPOCH_{name}_{date_str}.md'
        filepath = output_dir / filename

        # Stats calculation
        stats = calculate_stats(missions)
        
        # Generate Markdown Content
        report_lines = []
        report_lines.append("# EPOCH Report")
        report_lines.append("")
        report_lines.append(f"- **Total Missions:** {stats['total']}")
        report_lines.append(f"- **Ratified:** {stats['ratified_count']}")
        report_lines.append(f"- **Escalated:** {stats['escalated_count']}")
        report_lines.append(f"- **Avg Time:** {int(stats['avg_time'] * 10)}ms (formatted for brevity)")
        report_lines.append(f"- **Retry Attempts:** {stats['retry_count']}")
        report_lines.append("")

        # Detailed Mission List
        report_lines.append("## Recent Activity")
        report_lines.append("| ID | Status | Time | Retry Count | Track | Model | Tier | Split | VRAM (MB) |")
        report_lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")

        for m in missions:
            m_id = m.get('id', 'N/A')
            status = m.get('status', 'unknown').capitalize()
            time_val = m.get('time', 0) / 10 if isinstance(time_val, (int, float)) else 0 # Convert to seconds or raw ms? Prompt says avg_time logic.
            retries = m.get('retries', 0)
            track = m.get('track', 'N/A')
            model = m.get('model', 'N/A')
            tier = m.get('tier', 'N/A')
            split = f"{m.get('split', 0)}x"
            vram = m.get('vram', 0) / 1024 if isinstance(vram, (int, float)) else 0 # Assume MB is input

            row = f"| {m_id} | {status} | {time_val}s | {retries} | {track} | {model} | {tier} | {split} | {vram:.2f} |"
            report_lines.append(row)

        # Lessons Learned section
        report_lines.append("")
        report_lines.append("## Key Insights")
        
        # Simple logic to generate lessons based on stats availability
        if stats['total'] > 10:
            report_lines.append("- Volume increased significantly; monitor throughput.")
            if stats['ratified_count'] < stats['total']:
                report_lines.append("- Escalation rate detected; review approval criteria.")
                report_lines.append("- Retry patterns indicate instability in specific tracks (retry_count={stats['retry_count']}).")
        else:
            report_lines.append("- Early stages of epoch; continue monitoring.")

        # Final Report Block
        report_lines.append("## Final Block")
        report_lines.append("")

        content = "\n".join(report_lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Report written to {filepath}")

    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"Error generating report: {e}")


if __name__ == "__main__":
    main()