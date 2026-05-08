#!/usr/bin/env python3
"""
Generate N synthetic documents from templates for scale testing.

Usage:
    python scripts/generate_synthetic_docs.py --count 100 --output scripts/datasets/large

No API calls are made — all content is assembled from seed templates
with programmatic perturbation. Total cost: $0.
"""

import argparse
import os
import random
from datetime import datetime, timedelta

random.seed(42)

# ---------------------------------------------------------------------------
# Seed templates — realistic content, written once, no LLM cost
# ---------------------------------------------------------------------------

TEMPLATES = {
    "company_policy": [
        """## {company} {policy_name} Policy

**Effective Date**: {date}
**Version**: {version}
**Department**: {department}

### 1. Purpose

This policy establishes guidelines for {topic_summary} within {company}. All employees, contractors, and temporary staff must comply with these requirements.

### 2. Scope

This policy applies to all individuals who {scope_condition} on behalf of {company}, including full-time employees, part-time staff, contingent workers, and third-party vendors accessing {company} systems.

### 3. Policy Requirements

{requirements}

### 4. Compliance and Enforcement

Violations of this policy may result in disciplinary action, up to and including termination of employment and legal action. Employees must report potential violations to {reporting_channel} within {reporting_window}.

### 5. Definitions

- **{term1}**: {def1}
- **{term2}**: {def2}

### 6. Review Cycle

This policy will be reviewed {review_frequency} by the {department} team. Suggestions for improvement should be submitted via the company's policy feedback system.

---

*{company} is committed to maintaining a safe, productive, and compliant work environment.*""",
    ],
    "technical_doc": [
        """# {component_name} — Technical Specification

**Author**: {author}
**Last Updated**: {date}
**Status**: {status}

## Overview

{component_name} is a {component_type} that {component_purpose}. It is designed to meet the following requirements:

{requirements_list}

## Architecture

The system consists of {num_components} primary components:

{architecture_detail}

## Performance Characteristics

| Metric | Target | Method |
|--------|--------|--------|
| Throughput | {throughput} | Measured under standard load |
| Latency p50 | {latency_p50} | Averaged over 1-hour window |
| Latency p95 | {latency_p95} | Measured under peak load |
| Availability | {availability} | Calculated monthly |

## Configuration

```yaml
{config_example}
```

## Dependencies

- **Runtime**: {runtime_dep}
- **Storage**: {storage_dep}
- **Monitoring**: {monitor_dep}

## Deployment

{deployment_notes}

---

*For operational questions, contact the {team_name} team.*""",
    ],
    "product_faq": [
        """# {product_name} — Frequently Asked Questions

**Last Updated**: {date}
**Product Version**: {product_version}

## General

**Q: What is {product_name}?**
A: {product_name} is a {product_category} designed to {product_purpose}. It helps {target_users} achieve {key_benefit}.

**Q: Who is {product_name} for?**
A: {product_name} is designed for {target_audience_detail}. Typical users include {user_examples}.

**Q: What platforms does {product_name} support?**
A: Currently, {product_name} supports {platforms}. We are actively working on {future_platform}.

## Features

**Q: What are the key features?**
A: {feature_list}

**Q: Does {product_name} support {advanced_feature}?**
A: {advanced_feature_answer}

## Pricing

**Q: How much does {product_name} cost?**
A: {pricing_detail}

**Q: Is there a free trial?**
A: {trial_info}

## Support

**Q: What support options are available?**
A: {support_options}

**Q: How do I report a bug?**
A: {bug_reporting}

---

*For additional questions, visit our documentation portal or contact support.*""",
    ],
    "legal_doc": [
        """# {agreement_type}

**Parties**: {party_a} and {party_b}
**Effective Date**: {date}
**Jurisdiction**: {jurisdiction}

## 1. Definitions

Unless otherwise defined herein, capitalized terms shall have the following meanings:

- **"{term1}"** shall mean {def1}
- **"{term2}"** shall mean {def2}
- **"{term3}"** shall mean {def3}

## 2. {section_title_1}

{section_1_content}

## 3. {section_title_2}

{section_2_content}

## 4. Term and Termination

This agreement shall commence on the Effective Date and continue for an initial term of {initial_term}. Either party may terminate this agreement upon {notice_period} written notice if the other party materially breaches any provision hereof.

## 5. Limitation of Liability

{limitation_text}

## 6. Governing Law

This agreement shall be governed by and construed in accordance with the laws of {jurisdiction}.

---

*IN WITNESS WHEREOF, the parties have executed this agreement as of the Effective Date.*""",
    ],
    "industry_report": [
        """# Industry Brief: {industry_sector}

**Prepared by**: {prepared_by}
**Date**: {date}
**Classification**: {classification}

## Executive Summary

The {industry_sector} sector is experiencing significant transformation driven by {macro_trend}. Our analysis indicates that {key_finding}. Organizations that {recommended_action} are positioned to capture {opportunity_size} in value over the next {time_horizon}.

## Market Overview

The global {industry_sector} market was valued at {market_size_current} in {current_year} and is projected to reach {market_size_future} by {future_year}, growing at a CAGR of {cagr}. Key growth drivers include:

{growth_drivers}

## Competitive Landscape

{competitive_landscape}

## Key Recommendations

1. {rec_1}
2. {rec_2}
3. {rec_3}

## Risk Factors

{risk_factors}

---

*This report is confidential and intended for internal use only. Data sources include {data_sources}.*""",
    ],
}

# ---------------------------------------------------------------------------
# Replacement values for perturbation
# ---------------------------------------------------------------------------

COMPANIES = [
    "AcmeCorp",
    "NexGen Solutions",
    "Pinnacle Systems",
    "Vertex Industries",
    "Atlas Technologies",
    "Meridian Global",
    "Crestview Partners",
    "Polaris Dynamics",
    "Apex Innovations",
    "Summit Software",
    "Horizon Healthcare",
    "Frontier Analytics",
]

DEPARTMENTS = [
    "Engineering",
    "Information Security",
    "Human Resources",
    "Legal",
    "Compliance",
    "Product Management",
    "Operations",
    "Data Science",
]

POLICIES = [
    ("AI Usage", "the responsible use of artificial intelligence tools"),
    ("Data Security", "protecting company and customer data from unauthorized access"),
    ("Remote Work", "expectations and requirements for remote work arrangements"),
    ("Code of Conduct", "ethical standards and professional behavior expectations"),
    ("Acceptable Use", "proper use of company technology resources"),
    ("Privacy", "handling of personal and sensitive information"),
    ("Social Media", "appropriate use of social media in a professional context"),
    ("Travel and Expense", "guidelines for business travel and expense reimbursement"),
]

TOPICS = [
    "data analysis and reporting, document drafting and editing, and research",
    "secure handling of confidential information, data classification, and access control",
    "maintaining productivity, communication standards, and work-from-home setup requirements",
    "professional integrity, conflict of interest disclosure, and anti-harassment standards",
    "internet usage, software installation, and personal device management",
    "data collection, storage, retention, and sharing with third parties",
    "personal vs professional social media use, disclosure requirements, and content guidelines",
    "travel booking, expense categories, approval workflows, and reimbursement timelines",
]

REQUIREMENTS_SETS = [
    "All employees must complete annual training on this policy. Managers are responsible for ensuring their teams understand and adhere to these guidelines. Violations must be reported within 24 hours. Non-compliance may result in corrective action including suspension or termination.",
    "Employees must obtain written approval before engaging in activities covered by this policy. Regular audits will be conducted to ensure compliance. Exceptions require VP-level approval and must be documented in writing.",
    "All systems and processes affected by this policy must be reviewed quarterly. Access logs must be retained for a minimum of 90 days. Automated alerts will be triggered for any policy violations.",
    "Contractors and third parties accessing company systems must sign an acknowledgment of this policy. Annual attestation is required from all personnel. Training completion must be tracked in the company LMS.",
]

TERMS_DEFS = [
    (
        "Authorized Personnel",
        "Individuals who have completed required training and received written authorization.",
    ),
    (
        "Sensitive Information",
        "Any data that if disclosed could cause harm to the company, its employees, or its customers.",
    ),
    (
        "Access Control",
        "The process of granting and revoking permissions to systems and data based on role and necessity.",
    ),
    (
        "Data Breach",
        "Any unauthorized access, disclosure, or acquisition of company or customer data.",
    ),
    (
        "Conflict of Interest",
        "A situation where personal interests could improperly influence professional decisions.",
    ),
    (
        "Retention Period",
        "The duration for which records must be maintained before secure disposal.",
    ),
]

CHANNELS = [
    "the IT Security team via security@company.com",
    "the Legal department via legal@company.com",
    "the Compliance hotline at 1-800-COMPLY",
    "an anonymous reporting portal at ethics.company.com",
]

REVIEW_FREQUENCIES = ["annually", "semi-annually", "quarterly", "every 18 months"]

# Technical doc templates
COMPONENT_TYPES = [
    "distributed data processing pipeline",
    "real-time inference service",
    "RESTful API gateway",
    "stream processing engine",
    "batch analytics platform",
    "event-driven notification system",
]

COMPONENT_PURPOSES = [
    "processes and transforms large volumes of structured and unstructured data in real time",
    "serves machine learning model predictions with sub-100ms latency at scale",
    "provides authenticated, rate-limited access to internal microservices",
    "ingests events from multiple sources and routes them to downstream consumers",
    "aggregates metrics from distributed sources and generates actionable reports",
]

PERF_CONFIGS = [
    ("10,000 req/s", "15ms", "45ms", "99.95%"),
    ("5,000 req/s", "25ms", "80ms", "99.9%"),
    ("2,000 req/s", "50ms", "150ms", "99.99%"),
    ("20,000 req/s", "10ms", "30ms", "99.95%"),
    ("1,000 req/s", "100ms", "300ms", "99.5%"),
]

YAML_CONFIGS = [
    "server:\n  port: 8080\n  workers: 4\n  max_connections: 100\ntimeout: 30s\nretry_policy:\n  max_retries: 3\n  backoff: exponential",
    "database:\n  host: primary.db.internal\n  port: 5432\n  pool_size: 20\n  ssl: true\ncache:\n  ttl: 300\n  backend: redis",
    "logging:\n  level: INFO\n  format: json\n  outputs:\n    - stdout\n    - elasticsearch\nmetrics:\n  enabled: true\n  port: 9090",
    "auth:\n  provider: oauth2\n  jwks_url: https://auth.company.com/.well-known/jwks.json\n  token_ttl: 3600\ntls:\n  cert: /etc/certs/server.crt\n  key: /etc/certs/server.key",
    "storage:\n  engine: s3\n  bucket: data-lake-prod\n  region: us-east-1\n  compression: gzip\nretention:\n  hot: 7d\n  warm: 30d\n  cold: 365d",
]

AUTHORS = [
    "A. Patel",
    "M. Johansson",
    "K. Chen",
    "S. Rodriguez",
    "D. Thompson",
    "L. Kowalski",
    "R. Nakamura",
    "C. O'Brien",
]

STATUSES = ["Draft", "Under Review", "Approved", "Deprecated"]

TEAMS = [
    "Infrastructure",
    "Platform",
    "SRE",
    "Data Engineering",
    "ML Engineering",
    "Security",
]

# Product FAQ templates
PRODUCTS = [
    (
        "DataForge",
        "ETL and data transformation platform",
        "engineers build and maintain reliable data pipelines",
    ),
    (
        "ModelServe",
        "ML model deployment and serving platform",
        "data scientists deploy models to production in minutes",
    ),
    (
        "QueryGrid",
        "distributed SQL query engine",
        "analysts run complex queries across multiple data sources",
    ),
    (
        "WatchTower",
        "infrastructure monitoring and alerting system",
        "SRE teams detect and respond to incidents faster",
    ),
    (
        "AccessHub",
        "identity and access management solution",
        "security teams manage permissions across cloud services",
    ),
]

TARGET_AUDIENCES = [
    "data engineers and analytics teams at mid-to-large enterprises",
    "machine learning teams that need reliable model serving infrastructure",
    "organizations with complex data landscapes spanning multiple warehouses",
    "companies running critical infrastructure who need real-time observability",
    "regulated industries requiring audit-grade access controls",
]

PLATFORM_SETS = [
    ("Linux, macOS, and Windows via CLI", "WebAssembly runtime"),
    ("Kubernetes (Helm chart) and Docker Compose", "a serverless offering"),
    ("Python SDK, REST API, and GraphQL", "a Go client library"),
    ("AWS, GCP, and Azure", "on-premises deployment options"),
    ("Linux and macOS", "Windows Server support"),
]

ADVANCED_FEATURES = [
    "real-time streaming",
    "multi-region replication",
    "custom plugin development",
    "automated rollback",
    "cross-account access",
    "schema drift detection",
]

PRICING_OPTIONS = [
    "Free tier (1 project, 7-day retention). Pro at $49/user/month. Enterprise: custom pricing.",
    "Open source core with managed cloud at $0.10/credit. Free tier includes 10,000 credits/month.",
    "Usage-based pricing starting at $0.05 per 1,000 API calls. Volume discounts available for >1M calls/month.",
    "Flat $999/month for up to 5 users and 100 GB storage. Enterprise: custom with dedicated support.",
    "Free for open source projects. Commercial licenses start at $199/developer/year.",
]

TRIAL_OPTIONS = [
    "Yes, a 30-day free trial with full feature access. No credit card required.",
    "We offer a 14-day trial with limited features. Upgrade anytime to unlock the full platform.",
    "The free tier is available indefinitely with basic features. Premium features are unlocked during a 30-day trial.",
    "We provide a sandbox environment for evaluation. Contact sales for extended evaluation access.",
]

SUPPORT_CHOICES = [
    "Standard: email support with 24-hour SLA. Premium: 24/7 phone and chat support with 1-hour SLA. Enterprise: dedicated account manager and priority support.",
    "Community support via Discord and GitHub Issues. Pro customers get email support within 8 hours. Enterprise includes a named support engineer.",
    "Documentation, community forum, and email support during business hours. Premium tiers include 24/7 support with 4-hour SLA.",
    "In-app chat support for all users. Enterprise customers receive a dedicated Slack channel and monthly business reviews.",
]

BUG_REPORTING = [
    "File an issue on our GitHub repository or use the in-app feedback tool. Include logs and reproduction steps.",
    "Use the Support portal at support.company.com. Critical issues can be escalated via the emergency hotline.",
    "Submit a ticket through the dashboard. Security vulnerabilities should be reported via our responsible disclosure program.",
]

# Legal docs
AGREEMENT_TYPES = [
    "Software as a Service Agreement",
    "Data Processing Addendum",
    "Non-Disclosure Agreement",
    "Master Services Agreement",
    "Independent Contractor Agreement",
    "Service Level Agreement",
]

JURISDICTIONS = [
    "New York",
    "California",
    "Delaware",
    "England and Wales",
    "Singapore",
    "Germany",
]

LEGAL_SECTIONS = [
    (
        "Services and Obligations",
        "Provider shall perform the services described in Exhibit A with reasonable skill and care.",
    ),
    (
        "Fees and Payment",
        "Customer shall pay the fees set forth in the applicable Order Form within 30 days of invoice date.",
    ),
    (
        "Confidentiality",
        "Each party agrees to hold the other's Confidential Information in strict confidence for a period of 3 years.",
    ),
    (
        "Intellectual Property",
        "Each party retains all rights to its pre-existing intellectual property. No license is implied.",
    ),
    (
        "Data Protection",
        "Both parties shall comply with applicable data protection laws including GDPR and CCPA.",
    ),
    (
        "Warranties and Disclaimers",
        "Services are provided 'as is' without warranty of any kind, express or implied.",
    ),
]

INITIAL_TERMS = ["12 months", "24 months", "36 months", "1 year", "2 years"]
NOTICE_PERIODS = ["30 days'", "60 days'", "90 days'", "45 days'"]
LIMITATIONS = [
    "Neither party shall be liable for indirect, incidental, or consequential damages. Total liability shall not exceed the fees paid during the 12 months preceding the claim.",
    "Each party's aggregate liability shall be limited to $1,000,000 USD. This limitation does not apply to breaches of confidentiality or indemnification obligations.",
    "Liability is capped at the total amount paid under this agreement. No liability for loss of profits, data, or business opportunity.",
]

# Industry report templates
INDUSTRIES = [
    (
        "Enterprise AI/ML",
        "the rapid adoption of generative AI across enterprise workflows",
    ),
    (
        "Cloud Computing",
        "the shift toward multi-cloud and edge computing architectures",
    ),
    (
        "Cybersecurity",
        "increasing sophistication of cyber threats and regulatory requirements",
    ),
    (
        "Healthcare Technology",
        "digital transformation accelerated by AI-powered diagnostics",
    ),
    (
        "Financial Technology",
        "embedded finance and open banking reshaping traditional banking",
    ),
    (
        "Data Infrastructure",
        "the growing demand for real-time data processing and analytics",
    ),
]

KEY_FINDINGS = [
    "organizations that adopted AI-augmented workflows in 2025 saw 34% higher productivity gains than peers who did not",
    "enterprise cloud spend exceeded $800B globally, with 72% of organizations now running multi-cloud environments",
    "the average cost of a data breach reached $5.2M, driving increased investment in zero-trust architectures",
    "AI-assisted diagnostic tools reduced average time-to-diagnosis by 40% across major hospital systems",
    "embedded finance revenue grew 3.2x year-over-year, with non-financial brands leading adoption",
    "real-time data platforms overtook batch processing for the first time, representing 58% of new deployments",
]

RECOMMENDATIONS = [
    "Invest in AI governance frameworks before scaling AI initiatives beyond pilot phases",
    "Adopt a cloud-agnostic architecture strategy to maintain negotiating leverage with providers",
    "Implement zero-trust security models and conduct regular third-party penetration testing",
    "Build cross-functional AI evaluation teams that include domain experts, not just engineers",
    "Develop embedded finance partnerships early to capture first-mover advantage in your vertical",
    "Migrate legacy batch ETL pipelines to streaming architectures to remain competitive",
]

GROWTH_DRIVERS_SETS = [
    "- Increasing enterprise adoption of AI copilots and assistants\n- Declining cost of inference driving broader deployment\n- Regulatory frameworks creating compliance-driven demand",
    "- Digital transformation initiatives accelerating cloud migration\n- Edge computing reducing latency for IoT applications\n- Kubernetes maturation enabling workload portability",
    "- Ransomware attack frequency increasing 27% year-over-year\n- Regulatory penalties creating board-level urgency\n- Insurance requirements mandating specific security controls",
    "- AI-powered diagnostic tools receiving regulatory approval\n- Aging population driving healthcare demand\n- Interoperability mandates enabling data sharing across systems",
    "- Open banking regulations expanding across 60+ jurisdictions\n- Consumer demand for embedded financial experiences\n- API-first architectures reducing integration costs",
    "- Real-time decision making becoming a competitive necessity\n- Open table formats (Iceberg, Delta) standardizing data lakes\n- GPU-accelerated processing enabling faster insights",
]

COMPETITIVE_LANDSCAPE_SETS = [
    "The market is fragmented with no single player holding more than 15% share. Incumbent vendors are racing to add AI features, while startups focus on specific vertical use cases.",
    "Three major providers account for 67% of market share. The remaining 33% is distributed among 40+ niche providers competing on specialization and customer service.",
    "A two-tier market has emerged: enterprise-grade platforms with comprehensive feature sets and lightweight, open source alternatives that trade depth for simplicity.",
    "Open source alternatives are gaining traction, now representing 23% of new deployments. Incumbents are responding with more generous free tiers and community programs.",
]

RISK_FACTORS_SETS = [
    "Regulatory uncertainty remains the primary risk, with multiple jurisdictions developing conflicting AI governance frameworks. Supply chain concentration in GPU manufacturing creates hardware availability risk.",
    "Skills shortage in specialized areas (AI/ML, security) is constraining growth. Economic headwinds may slow enterprise procurement cycles in the near term.",
    "Data sovereignty regulations are fragmenting the market, requiring local infrastructure investments. Rapid technology change risks obsolescence of current architectures.",
]

DATA_SOURCES = [
    "Gartner, Forrester, IDC, and internal market analysis",
    "McKinsey Global Institute, Statista, SEC filings, and industry surveys",
    "CB Insights, PitchBook, S&P Global, and partner ecosystem data",
    "Crunchbase, Bloomberg, internal TAM/SAM analysis, and customer interviews",
]

# Domains for structured variation
DOMAINS = ["policy", "tech", "faq", "legal", "report"]

# ---------------------------------------------------------------------------
# Date generation
# ---------------------------------------------------------------------------


def random_date(start_year: int = 2024, end_year: int = 2026) -> str:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.strftime("%B %d, %Y")


# ---------------------------------------------------------------------------
# Document builders
# ---------------------------------------------------------------------------


def build_policy(doc_id: int) -> str:
    company = random.choice(COMPANIES)
    policy_name, topic_summary = random.choice(POLICIES)
    department = random.choice(DEPARTMENTS)
    term1, def1 = random.choice(TERMS_DEFS)
    term2, def2 = random.choice(TERMS_DEFS)
    return random.choice(TEMPLATES["company_policy"]).format(
        company=company,
        policy_name=policy_name,
        date=random_date(),
        version=f"{random.randint(1, 4)}.{random.randint(0, 9)}",
        department=department,
        topic_summary=topic_summary,
        scope_condition=random.choice(
            [
                "develop, deploy, or maintain software systems",
                "handle, process, or store company or customer data",
                "communicate on behalf of the company in any capacity",
                "access company networks, systems, or physical facilities",
            ]
        ),
        requirements=random.choice(REQUIREMENTS_SETS),
        reporting_channel=random.choice(CHANNELS),
        reporting_window=random.choice(
            [
                "within 24 hours",
                "immediately",
                "within one business day",
                "as soon as practicable",
            ]
        ),
        term1=term1,
        def1=def1,
        term2=term2,
        def2=def2,
        review_frequency=random.choice(REVIEW_FREQUENCIES),
    )


def build_technical_doc(doc_id: int) -> str:
    component_name = f"{random.choice(['Apex', 'Nova', 'Fusion', 'Helix', 'Titan', 'Onyx', 'Dynamo', 'Zenith'])}-{random.randint(1000, 9999)}"
    component_type = random.choice(COMPONENT_TYPES)
    component_purpose = random.choice(COMPONENT_PURPOSES)
    throughput, lat_p50, lat_p95, avail = random.choice(PERF_CONFIGS)

    num_sub = random.randint(3, 6)
    sub_components = []
    for i in range(num_sub):
        sub_components.append(
            f"- **{chr(65 + i)}**: {random.choice(COMPONENT_PURPOSES)}"
        )
    architecture_detail = "\n".join(sub_components)

    return random.choice(TEMPLATES["technical_doc"]).format(
        component_name=component_name,
        author=random.choice(AUTHORS),
        date=random_date(),
        status=random.choice(STATUSES),
        component_type=component_type,
        component_purpose=component_purpose,
        requirements_list="\n".join(
            f"- {r}"
            for r in random.sample(
                [
                    "Process at least 10,000 events per second with <1% error rate",
                    "Support horizontal scaling with zero downtime deployments",
                    "Provide comprehensive observability via OpenTelemetry traces",
                    "Maintain data durability with at-least-once delivery guarantees",
                    "Authenticate all requests via OAuth2 with role-based access control",
                    "Support pluggable output sinks via a well-defined interface",
                    "Audit all state-changing operations with immutable logs",
                ],
                k=random.randint(3, 5),
            )
        ),
        num_components=num_sub,
        architecture_detail=architecture_detail,
        throughput=throughput,
        latency_p50=lat_p50,
        latency_p95=lat_p95,
        availability=avail,
        config_example=random.choice(YAML_CONFIGS),
        runtime_dep=random.choice(
            [
                "Python 3.11+",
                "Rust with Tokio async runtime",
                "Go 1.22 with standard library",
                "Java 21 with Spring Boot 3.x",
            ]
        ),
        storage_dep=random.choice(
            [
                "PostgreSQL 16 with TimescaleDB",
                "Apache Iceberg on S3-compatible storage",
                "Redis Cluster 7.2+ for caching layer",
                "Kafka 3.6+ with Tiered Storage",
            ]
        ),
        monitor_dep=random.choice(
            [
                "Prometheus + Grafana with custom dashboards",
                "Datadog with APM and log management",
                "OpenTelemetry collector exporting to Tempo",
                "ELK stack with custom index templates",
            ]
        ),
        deployment_notes=random.choice(
            [
                "Deployed via Helm chart to Kubernetes cluster. Canary deployments with 10% traffic shift. Rollback via `kubectl rollout undo`.",
                "Packaged as Docker container. Deployed via Docker Compose for staging, Helm for production. Blue-green deployment strategy.",
                "Serverless deployment on AWS Lambda with provisioned concurrency. Terraform-managed infrastructure. Multi-region active-active.",
                "Deployed to bare-metal instances behind a load balancer. Ansible-managed configuration. Rolling updates with 20% batch size.",
            ]
        ),
        team_name=random.choice(TEAMS),
    )


def build_faq(doc_id: int) -> str:
    product_name, product_category, product_purpose = random.choice(PRODUCTS)
    target_audience = random.choice(TARGET_AUDIENCES)
    platforms, future_platform = random.choice(PLATFORM_SETS)
    advanced_feature = random.choice(ADVANCED_FEATURES)
    features = random.sample(
        [
            "Real-time data synchronization across multiple regions",
            "Role-based access control with granular permissions",
            "Automated backup and disaster recovery",
            "Custom webhook integrations with external systems",
            "Built-in monitoring and alerting dashboards",
            "API-first design with comprehensive SDK support",
            "Multi-tenant isolation with dedicated compute resources",
            "Audit logging with 90-day retention",
        ],
        k=random.randint(3, 5),
    )

    return random.choice(TEMPLATES["product_faq"]).format(
        product_name=product_name,
        product_version=f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
        date=random_date(),
        product_category=product_category,
        product_purpose=product_purpose,
        target_users=random.choice(
            [
                "data teams",
                "engineering organizations",
                "enterprise security teams",
                "platform engineers",
            ]
        ),
        key_benefit=random.choice(
            [
                "accelerate development cycles",
                "reduce operational overhead",
                "improve system reliability",
                "maintain compliance",
            ]
        ),
        target_audience_detail=target_audience,
        user_examples=random.choice(
            [
                "data engineers, analysts, and data scientists",
                "backend engineers and DevOps practitioners",
                "security analysts and compliance officers",
                "SRE teams and platform engineers",
            ]
        ),
        platforms=platforms,
        future_platform=future_platform,
        feature_list="\n".join(f"- {f}" for f in features),
        advanced_feature=advanced_feature,
        advanced_feature_answer=random.choice(
            [
                f"Yes, {product_name} supports {advanced_feature} in the Enterprise tier. Contact sales for a demo.",
                f"{advanced_feature.capitalize()} is on our Q{random.randint(1, 4)} roadmap. Join the early access program to get notified.",
                f"Not yet, but we are actively developing {advanced_feature}. Sign up for our newsletter for updates.",
            ]
        ),
        pricing_detail=random.choice(PRICING_OPTIONS),
        trial_info=random.choice(TRIAL_OPTIONS),
        support_options=random.choice(SUPPORT_CHOICES),
        bug_reporting=random.choice(BUG_REPORTING),
    )


def build_legal_doc(doc_id: int) -> str:
    party_a = random.choice(COMPANIES)
    party_b = random.choice([c for c in COMPANIES if c != party_a])
    section_title_1, section_1_content = random.choice(LEGAL_SECTIONS)
    section_title_2, section_2_content = random.choice(LEGAL_SECTIONS)

    return random.choice(TEMPLATES["legal_doc"]).format(
        agreement_type=random.choice(AGREEMENT_TYPES),
        party_a=party_a,
        party_b=party_b,
        date=random_date(),
        jurisdiction=random.choice(JURISDICTIONS),
        term1=random.choice(
            [
                "Confidential Information",
                "Intellectual Property",
                "Service Level",
                "Fees",
                "Documentation",
            ]
        ),
        def1=random.choice(
            [
                "Any information disclosed by one party to the other that is marked confidential or reasonably should be understood to be confidential.",
                "All patents, copyrights, trademarks, trade secrets, and other proprietary rights recognized under applicable law.",
                "The performance metrics and availability targets set forth in the applicable Service Level Agreement.",
            ]
        ),
        term2=random.choice(
            ["Effective Date", "Order Form", "Statement of Work", "Change Order"]
        ),
        def2=random.choice(
            [
                "The date on which both parties have executed this agreement.",
                "A document executed by both parties that specifies the services, fees, and other commercial terms.",
                "A written description of work to be performed, attached to and incorporated into this agreement.",
            ]
        ),
        term3=random.choice(["Indemnification", "Force Majeure", "Material Breach"]),
        def3=random.choice(
            [
                "The obligation of one party to compensate the other for losses arising from third-party claims.",
                "An event beyond a party's reasonable control that prevents performance of obligations.",
                "A failure to perform a material obligation that is not cured within the applicable cure period.",
            ]
        ),
        section_title_1=section_title_1,
        section_1_content=section_1_content,
        section_title_2=section_title_2,
        section_2_content=section_2_content,
        initial_term=random.choice(INITIAL_TERMS),
        notice_period=random.choice(NOTICE_PERIODS),
        limitation_text=random.choice(LIMITATIONS),
    )


def build_report(doc_id: int) -> str:
    industry_sector, macro_trend = random.choice(INDUSTRIES)
    company = random.choice(COMPANIES)
    current_year = 2026
    future_year = current_year + random.choice([3, 5, 7])

    return random.choice(TEMPLATES["industry_report"]).format(
        industry_sector=industry_sector,
        prepared_by=f"Strategic Insights Group, {company}",
        date=random_date(),
        classification=random.choice(
            ["Confidential", "Internal Only", "Client Privileged"]
        ),
        macro_trend=macro_trend,
        key_finding=random.choice(KEY_FINDINGS),
        recommended_action=random.choice(
            [
                "invest in AI governance",
                "adopt multi-cloud architectures",
                "implement zero-trust security",
                "build embedded finance capabilities",
            ]
        ),
        opportunity_size=random.choice(
            ["$50-80B", "$120-180B", "$200-350B", "$30-60B"]
        ),
        time_horizon=random.choice(["3-5 years", "5-7 years", "the next decade"]),
        market_size_current=random.choice(["$120B", "$340B", "$80B", "$210B", "$95B"]),
        current_year=current_year,
        market_size_future=random.choice(["$450B", "$890B", "$210B", "$620B"]),
        future_year=future_year,
        cagr=random.choice(["14.2%", "18.7%", "22.3%", "9.8%", "25.1%"]),
        growth_drivers=random.choice(GROWTH_DRIVERS_SETS),
        competitive_landscape=random.choice(COMPETITIVE_LANDSCAPE_SETS),
        rec_1=random.choice(RECOMMENDATIONS),
        rec_2=random.choice(RECOMMENDATIONS),
        rec_3=random.choice(RECOMMENDATIONS),
        risk_factors=random.choice(RISK_FACTORS_SETS),
        data_sources=random.choice(DATA_SOURCES),
    )


# ---------------------------------------------------------------------------
# Builders dispatch
# ---------------------------------------------------------------------------

BUILDERS = {
    "policy": build_policy,
    "tech": build_technical_doc,
    "faq": build_faq,
    "legal": build_legal_doc,
    "report": build_report,
}

FILE_TYPES = {
    "policy": ("txt", "text/plain"),
    "tech": ("md", "text/markdown"),
    "faq": ("md", "text/markdown"),
    "legal": ("txt", "text/plain"),
    "report": ("md", "text/markdown"),
}


def generate_document(doc_id: int, domain: str) -> tuple[str, str, str]:
    """Generate a single document. Returns (filename, content, mime_type)."""
    builder = BUILDERS[domain]
    ext, mime = FILE_TYPES[domain]
    content = builder(doc_id)
    filename = f"syn_{domain}_{doc_id:05d}.{ext}"
    return filename, content, mime


def generate_dataset(count: int, output_dir: str) -> None:
    """Generate `count` documents, evenly distributed across domains."""
    os.makedirs(output_dir, exist_ok=True)
    metadata = []

    per_domain = max(1, count // len(DOMAINS))
    docs_generated = 0

    for domain in DOMAINS:
        for i in range(per_domain):
            doc_id = docs_generated + 1
            filename, content, mime = generate_document(doc_id, domain)
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)
            metadata.append(
                {
                    "filename": filename,
                    "display_name": f"{domain.replace('_', ' ').title()} #{doc_id}",
                    "mime_type": mime,
                    "size_bytes": len(content),
                }
            )
            docs_generated += 1

    # Generate metadata CSV
    with open(os.path.join(output_dir, "metadata.csv"), "w") as f:
        f.write("filename,display_name,mime_type,size_bytes\n")
        for m in metadata:
            f.write(
                f"{m['filename']},{m['display_name']},{m['mime_type']},{m['size_bytes']}\n"
            )

    total_bytes = sum(m["size_bytes"] for m in metadata)
    print(f"Generated {docs_generated} documents in {output_dir}")
    print(
        f"  Size: {total_bytes / 1024:.1f} KB total, {total_bytes / docs_generated:.0f} bytes avg"
    )
    print(f"  Domains: {', '.join(DOMAINS)} (≈{per_domain} each)")
    print(f"  Metadata: {output_dir}/metadata.csv")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate synthetic documents for RAG scale testing"
    )
    parser.add_argument(
        "--count", type=int, default=100, help="Number of documents to generate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="scripts/datasets/large",
        help="Output directory for generated documents",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RAG Production Starter — Synthetic Document Generator")
    print("=" * 60)
    print(f"Generating {args.count} documents...")
    print("  (No API calls — all content from templates)")
    print()

    generate_dataset(args.count, args.output)

    print()
    print("Next step:")
    print(f"  python scripts/seed_demo.py --dataset-dir {args.output}")
    print("=" * 60)
