# 🍽️ Zomato AI Data Engineering Project

An end-to-end **Data Engineering + AI project** that processes Zomato-style data and builds an analytics-ready data platform with AI capabilities.

## 🚀 Pipeline

```text
Source Data → Amazon S3 → Snowflake → dbt → Airflow → AI
```
🛠️ Tech Stack
Amazon S3 – Raw data storage
Snowflake – Data warehouse
dbt – Data transformation and modeling
Apache Airflow – Pipeline orchestration
Docker – Airflow environment
Python – Data & AI processing
Google Gemini – Generative AI
Sentence Transformers – Review embeddings
Streamlit – AI applications
🤖 AI Features
Review Enrichment

Uses Gemini to analyze customer reviews and generate structured insights.

RAG Review Assistant

Uses Sentence Transformers + semantic search + Gemini to retrieve relevant customer reviews and generate answers.

Text-to-SQL

Allows users to ask questions about the Snowflake warehouse in natural language and generates SQL to retrieve the results.

❄️ Data Warehouse

Snowflake is organized into:

RAW
 ↓
STAGING
 ↓
MARTS

The project includes staging models, fact tables, dimension tables, and analytical marts for:

Orders
Revenue
Restaurants
Customers
Delivery performance
Reviews
🛠️ Airflow

Airflow orchestrates the pipeline using the zomato_batch DAG:

reload_raw → dbt_build_core

Airflow runs using Docker.

📁 Project Structure
├── ai/              # AI applications
├── airflow/         # Airflow DAG & Docker setup
├── snowflake/       # Snowflake SQL scripts
├── zomato/          # dbt project
├── .gitignore
└── README.md
🔐 Security

Credentials, datasets, logs, caches, and other generated files are excluded from GitHub.

Example configuration files are provided as:

.env.example
profiles.yml.example
⚙️ Main Commands
dbt
cd zomato
dbt debug
dbt build
Airflow
cd airflow
docker compose build
docker compose up -d
RAG
streamlit run ai/rag_chat.py
Text-to-SQL
streamlit run ai/text_to_sql.py
🎯 Project Goal

The project demonstrates how cloud data engineering, data warehousing, orchestration, and generative AI can be combined into a single end-to-end analytics platform.
