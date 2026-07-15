# FDE Intelligence Briefing: Snowflake

## FDE Readiness Score

**Grade: B — 82/100**

Snowflake is a mature, production-proven cloud data warehouse with strong enterprise adoption and a well-documented API ecosystem. Pricing complexity and potential Redshift migration effort are the main deployment considerations.

**Blockers:**
- ✗ Existing Redshift or BigQuery contracts may create switching friction — uncover contract end dates early
- ✗ Data residency requirements in regulated industries (healthcare, finance) need explicit Snowflake region mapping

**Accelerators:**
- ✓ Pre-built connectors for most enterprise ETL tools (Fivetran, dbt, Informatica)
- ✓ Large Snowflake partner ecosystem means client likely has internal champions
- ✓ Consumption-based pricing makes POC low-commitment

**Integration Complexity:** MEDIUM

## Executive Summary

Snowflake is a mature cloud data warehouse with strong enterprise traction and a well-documented integration ecosystem. Pricing is consumption-based and can scale unpredictably without query governance, which is the most common post-deployment complaint. The primary competitive threats are Databricks (for ML-heavy workloads) and Google BigQuery (for GCP-native clients), but Snowflake holds a strong position for pure analytics workloads.

## Technical Fit
_Confidence: high_

Snowflake operates on a separation of storage and compute architecture, allowing independent scaling of each. It supports all major cloud providers (AWS, GCP, Azure) and offers cross-cloud replication. Native connectors exist for Kafka, Spark, dbt, and most major ETL tools. The REST API and Python connector are well-documented and production-stable.

- Multi-cloud deployment supported (AWS, GCP, Azure) with cross-region replication
- Native Kafka connector for streaming ingestion without third-party tools
- dbt integration is first-class — most enterprise clients already use it
- Snowpark enables Python/Java/Scala workloads inside Snowflake compute
- Zero-copy cloning reduces environment provisioning from days to seconds
- SOC 2 Type II, HIPAA, PCI-DSS certified out of the box

**Sources:**
- https://docs.snowflake.com/en/user-guide/ecosystem
- https://www.snowflake.com/en/data-cloud/workloads/

## Cost Signals
_Confidence: medium_

Snowflake uses a credit-based consumption model. Compute is billed per virtual warehouse per second, with credits costing $2–$4 depending on tier. Storage is ~$23/TB/month on AWS. A mid-size enterprise (500–5,000 users) typically spends $150K–$600K annually depending on query volume and warehouse sizing.

- Compute credits: $2–4/credit depending on Enterprise vs Business Critical tier
- Storage: ~$23/TB/month (AWS us-east-1)
- Typical mid-enterprise annual spend: $150K–$600K
- Cost spikes common from runaway queries — warehouse auto-suspend settings are critical
- Enterprise tier (minimum $20K/year) required for multi-cluster warehouses and failover
- Discount negotiable at $100K+ commit — push for 20–30% off list

**Sources:**
- https://www.snowflake.com/pricing/
- https://cloudoptimizer.io/snowflake-pricing-guide-2025

## Risk Flags
_Confidence: high_

The most common enterprise deployment failure mode is uncontrolled cost growth from ungoverned warehouses. Security misconfigurations (public S3 bucket exposure via external stages) have caused data breaches at two Fortune 500 clients. Vendor lock-in is moderate — data is portable but Snowflake-specific SQL extensions create migration friction.

- Cost governance is the #1 post-deployment issue — resource monitors must be configured before go-live
- External stage misconfiguration has caused data exposure incidents — needs security review in deployment checklist
- Vendor lock-in via Snowflake-specific features (Snowpipe, Dynamic Tables, Cortex AI)
- Outage history: 3 significant incidents in 2023–2024, all on AWS us-east-1; multi-region failover mitigates
- Support tier matters — Enterprise support SLA is 1-hour for Sev-1; lower tiers are 4-hour

**Sources:**
- https://status.snowflake.com
- https://www.darkreading.com/cloud-security/snowflake-breach-2024

## Competitor Landscape
_Confidence: high_

Databricks is the primary threat for ML/AI-heavy workloads; BigQuery wins on GCP-native shops. Redshift is losing ground but entrenched in AWS shops with existing tooling. Snowflake holds the strongest position for pure analytics + data sharing use cases.

- **Databricks**: wins when client has active ML workloads — lakehouse architecture eliminates the ETL layer
- **Google BigQuery**: wins for GCP-native clients and serverless preference — no warehouse management overhead
- **Amazon Redshift**: entrenched in AWS-heavy shops but losing new deals — worse performance per dollar at scale
- **Clickhouse**: emerging threat for high-frequency analytics (time-series, product analytics) — 10x cheaper for right workloads
- Snowflake's data sharing (Data Marketplace) is a unique differentiator with no direct equivalent

**Sources:**
- https://www.gartner.com/reviews/market/cloud-database-management-systems
- https://db-engines.com/en/ranking/relational+dbms

## Recommended Client Questions

1. What is your current data warehouse (Redshift, BigQuery, on-prem)? When does that contract expire?
2. What is your monthly query volume and average warehouse size today — do you have cost benchmarks?
3. Do you have active ML or AI workloads that need to run close to the data, or is this pure analytics?
4. What data residency or compliance requirements apply — HIPAA, PCI, GDPR? Which regions are required?
5. Who owns query governance today — is there a platform team, or is it self-serve for analysts?
6. Have you evaluated Databricks? What made you lean toward Snowflake over the lakehouse approach?
