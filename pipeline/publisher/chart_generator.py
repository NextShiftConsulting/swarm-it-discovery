"""
RSCT Chart Generator - Visualization for Discovery Pipeline

Generates publication-ready RSCT charts for paper analysis batches.
Uses swarm-it-api's dashboard/rsct_charts.py for chart generation.

Integration with discovery pipeline:
1. Collect certificates from paper certifications
2. Generate batch analysis charts
3. Upload to S3 for website display
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add swarm-it-api to path
_api_path = os.path.expanduser("~/GitHub/swarm-it-api")
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

# Import from swarm-it-api
try:
    from dashboard.rsct_charts import RSCTCharts
    from analysis.builder import ReportBuilder
    from analysis.agents.analyzer import AnalyzerAgent
    HAS_SWARMIT_API = True
except ImportError as e:
    print(f"Warning: swarm-it-api not available: {e}")
    HAS_SWARMIT_API = False


@dataclass
class ChartBatch:
    """Result from chart generation."""
    batch_id: str
    date: str
    chart_paths: Dict[str, str] = field(default_factory=dict)
    s3_paths: Dict[str, str] = field(default_factory=dict)
    analysis_summary: Optional[str] = None
    certificates_count: int = 0


class DiscoveryChartGenerator:
    """
    Chart generator for discovery pipeline.

    Generates RSCT charts from batches of paper certifications.
    """

    CHART_TYPES = ["quality_kappa", "kappa_sigma", "gate_depth"]

    def __init__(
        self,
        output_dir: str = "content/charts",
        s3_bucket: str = "swarmit-nextshift-site",
        s3_prefix: str = "content/charts",
    ):
        self.output_dir = output_dir
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix

        if HAS_SWARMIT_API:
            self.charts = RSCTCharts()
            self.analyzer = AnalyzerAgent()
        else:
            self.charts = None
            self.analyzer = None

    def generate_batch_charts(
        self,
        certificates: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
        upload_s3: bool = True,
    ) -> ChartBatch:
        """
        Generate charts for a batch of certificates.

        Args:
            certificates: List of RSCT certificates from paper analysis
            batch_id: Optional batch identifier (default: today's date)
            upload_s3: Whether to upload to S3

        Returns:
            ChartBatch with paths to generated charts
        """
        if not HAS_SWARMIT_API:
            print("Warning: swarm-it-api not available, skipping chart generation")
            return ChartBatch(
                batch_id=batch_id or datetime.now().strftime("%Y-%m-%d"),
                date=datetime.now().isoformat(),
            )

        batch_id = batch_id or datetime.now().strftime("%Y-%m-%d")
        batch_dir = os.path.join(self.output_dir, batch_id)
        Path(batch_dir).mkdir(parents=True, exist_ok=True)

        result = ChartBatch(
            batch_id=batch_id,
            date=datetime.now().isoformat(),
            certificates_count=len(certificates),
        )

        # Generate analysis summary
        if self.analyzer and certificates:
            analysis = self.analyzer.analyze(certificates)
            result.analysis_summary = self.analyzer.summarize(analysis)

        # Get gate_reached from first cert for gauge
        gate_reached = 5
        if certificates:
            gate_reached = certificates[0].get("gate_reached", 5)

        # Generate each chart type
        for chart_type in self.CHART_TYPES:
            try:
                fig = self._generate_chart(chart_type, certificates, gate_reached)
                if fig is None:
                    continue

                # Save PNG and SVG
                for fmt in ["png", "svg"]:
                    filename = f"{chart_type}.{fmt}"
                    filepath = os.path.join(batch_dir, filename)

                    if fmt == "png":
                        fig.write_image(filepath, scale=2)
                    else:
                        fig.write_image(filepath)

                    result.chart_paths[filename] = filepath

            except Exception as e:
                print(f"Error generating {chart_type}: {e}")

        # Upload to S3 if requested
        if upload_s3 and result.chart_paths:
            result.s3_paths = self._upload_to_s3(result.chart_paths, batch_id)

        return result

    def _generate_chart(
        self,
        chart_type: str,
        certificates: List[Dict[str, Any]],
        gate_reached: int,
    ):
        """Generate a single chart by type."""
        if chart_type == "quality_kappa":
            return self.charts.quality_compatibility_quadrant(certificates)
        elif chart_type == "kappa_sigma":
            return self.charts.kappa_sigma_phase(certificates)
        elif chart_type == "gate_depth":
            return self.charts.gate_depth_gauge(gate_reached)
        elif chart_type == "capacity_competence":
            return self.charts.capacity_competence_quadrant()
        return None

    def _upload_to_s3(
        self,
        chart_paths: Dict[str, str],
        batch_id: str,
    ) -> Dict[str, str]:
        """Upload charts to S3."""
        s3_paths = {}

        try:
            import boto3
            try:
                from swarm_auth import get_aws_credentials
                aws_creds = get_aws_credentials()
                s3 = boto3.client("s3", **aws_creds)
            except Exception:
                s3 = boto3.client("s3")

            for filename, local_path in chart_paths.items():
                s3_key = f"{self.s3_prefix}/{batch_id}/{filename}"

                # Determine content type
                content_type = "image/png" if filename.endswith(".png") else "image/svg+xml"

                s3.upload_file(
                    local_path,
                    self.s3_bucket,
                    s3_key,
                    ExtraArgs={"ContentType": content_type},
                )

                s3_paths[filename] = f"s3://{self.s3_bucket}/{s3_key}"
                print(f"Uploaded: {s3_paths[filename]}")

        except ImportError:
            print("Warning: boto3 not available, skipping S3 upload")
        except Exception as e:
            print(f"S3 upload error: {e}")

        return s3_paths

    def generate_daily_report(
        self,
        certificates: List[Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate full daily report with charts and analysis.

        Uses swarm-it-api's ReportBuilder for comprehensive output.
        """
        if not HAS_SWARMIT_API:
            return "Report generation requires swarm-it-api"

        batch_id = datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join(self.output_dir, batch_id)

        report = (
            ReportBuilder()
            .with_certificates(certificates)
            .for_domain("research")
            .with_title(f"Daily Discovery Report - {batch_id}")
            .with_author("Discovery Pipeline")
            .with_charts(self.CHART_TYPES)
            .with_output(output_dir)
            .generate()
        )

        # Save report
        output_path = output_path or os.path.join(output_dir, "report.md")
        report.save(output_path)

        return output_path


# Convenience function for pipeline integration
def generate_discovery_charts(
    certificates: List[Dict[str, Any]],
    upload_s3: bool = True,
) -> ChartBatch:
    """
    Generate charts for discovery pipeline.

    Usage in pipeline/run.py:
        from publisher.chart_generator import generate_discovery_charts

        # After collecting certificates
        chart_batch = generate_discovery_charts(certificates)
        print(f"Charts: {chart_batch.chart_paths}")
    """
    generator = DiscoveryChartGenerator()
    return generator.generate_batch_charts(certificates, upload_s3=upload_s3)
