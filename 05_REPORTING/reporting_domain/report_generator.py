import os
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate(self, benchmark_result):
        """Alias — matches ratified test spec."""
        return self.generate_report(benchmark_result)

    def generate_report(self, benchmark_result):
        if not benchmark_result:
            raise ValueError("Benchmark result cannot be None")
        
        # Extract necessary information from benchmark result
        domain = benchmark_result.get('domain', 'Unknown')
        model = benchmark_result.get('model', 'Unknown')
        tier = benchmark_result.get('tier', 'Unknown')
        score = benchmark_result.get('score', 'Unknown')
        gate_results = benchmark_result.get('gate_results', 'Unknown')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Construct the markdown report
        report_content = "# Benchmark Report\n\n"
        report_content += f"## Domain: {domain}\n\n"
        report_content += f"## Model: {model}\n\n"
        report_content += f"## Tier: {tier}\n\n"
        report_content += f"## Score: {score}\n\n"
        report_content += f"## Gate Results: {gate_results}\n\n"
        report_content += f"## Timestamp: {timestamp}\n"
        
        # Write the report to the specified output directory
        report_filename = f"report_{timestamp.replace(' ', '_')}.md"
        report_path = os.path.join(self.output_dir, report_filename)
        with open(report_path, 'w') as report_file:
            report_file.write(report_content)
        
        return report_path

# Example usage
if __name__ == "__main__":
    benchmark_result = {
        'domain': '05_REPORTING',
        'model': 'GPT-3',
        'tier': 'Advanced',
        'score': '95',
        'gate_results': 'Passed'
    }
    
    report_generator = ReportGenerator('05_REPORTING/')
    report_path = report_generator.generate_report(benchmark_result)
    print(f"Report generated at: {report_path}")

