# 🍽️ Zomato AI Data Engineering Project

An end-to-end **Data Engineering + AI project** that processes Zomato-style data and builds a scalable, analytics-ready data platform with **cloud storage, data warehousing, transformation, orchestration, and Generative AI**.

---

## 🚀 Project Pipeline

```text
Source Data
     ↓
Amazon S3
     ↓
Snowflake
     ↓
    dbt
     ↓
Apache Airflow
     ↓
AI Applications
```

The pipeline combines modern data engineering technologies with AI to transform raw restaurant, order, customer, delivery, and review data into useful analytical and conversational applications.

---

## 🛠️ Tech Stack

| Technology                | Purpose                                       |
| ------------------------- | --------------------------------------------- |
| **Amazon S3**             | Raw data storage                              |
| **Snowflake**             | Cloud data warehouse                          |
| **dbt**                   | Data transformation and data modeling         |
| **Apache Airflow**        | Pipeline orchestration                        |
| **Docker**                | Containerized Airflow environment             |
| **Python**                | Data processing and AI applications           |
| **Google Gemini API**         | Generative AI and natural-language processing |
| **Sentence Transformers** | Review embeddings and semantic search         |
| **Streamlit**             | Interactive AI applications                   |

---

## ❄️ Data Warehouse Architecture

The Snowflake data warehouse follows a layered architecture:

```text
RAW
 │
 ▼
STAGING
 │
 ▼
MARTS
```

### RAW

Contains the raw data loaded from Amazon S3.

### STAGING

Cleans and standardizes raw data before it is used for analytical models.

### MARTS

Contains business-ready fact tables, dimension tables, and analytical marts.

The warehouse includes models for:

* 📦 Orders
* 💰 Revenue
* 🍽️ Restaurants
* 👤 Customers
* 🚚 Delivery Performance
* ⭐ Reviews

---

## 🤖 AI Features

### 1. 📝 Review Enrichment

Uses **Google Gemini** to analyze customer reviews and generate structured insights.

The review enrichment process can extract information such as:

* Sentiment
* Review categories
* Key topics
* Customer feedback
* Structured labels

This transforms unstructured customer reviews into data that can be analyzed alongside the warehouse data.

---

### 2. 💬 RAG Review Assistant

A **Retrieval-Augmented Generation (RAG)** application that allows users to ask questions about customer reviews.

The application uses:

```text
Customer Reviews
      ↓
Sentence Transformers
      ↓
Review Embeddings
      ↓
Semantic Search
      ↓
Relevant Reviews
      ↓
Google Gemini
      ↓
AI-generated Answer
```

Users can ask natural-language questions and retrieve relevant reviews before Gemini generates the final response.

The RAG application is built with **Streamlit**.

---

### 3. 🧠 Text-to-SQL

Allows users to interact with the Snowflake data warehouse using natural language.

For example:

```text
"Which restaurants generated the highest revenue?"
```

The application uses Gemini to generate an SQL query that can retrieve the required information from Snowflake.

The workflow is:

```text
Natural Language Question
          ↓
       Gemini
          ↓
      SQL Query
          ↓
       Snowflake
          ↓
      Query Result
          ↓
    User-friendly Output
```

This provides a natural-language interface for exploring analytical data.

---

## 🛠️ Apache Airflow

**Apache Airflow** is used to orchestrate the data pipeline.

The project includes a DAG called:

```text
zomato_batch
```

### Pipeline

```text
reload_raw
     ↓
dbt_build_core
     ↓
enrich_reviews
     ↓
dbt_build_ai
```

### `reload_raw`

Reloads the required raw data into the Snowflake RAW layer.

### `dbt_build_core`

Runs the dbt transformation pipeline to build the staging, core, and analytical models.

Airflow runs inside a **Docker** environment, making the orchestration setup easier to reproduce.

### `enrich_reviews`

Uses Google Gemini to analyze and enrich customer reviews with AI-generated insights.

### `dbt_build_ai`

Runs the dbt models tagged with `ai`, preparing the data required by the project's **AI applications, including RAG and Text-to-SQL**.

---

## 🐳 Docker

The Airflow environment is containerized using Docker.

Start the Airflow environment with:

```bash
cd airflow

docker compose build
docker compose up -d
```

---

## 📁 Project Structure

```text
zomato-ai-data-engineering/
│
├── ai/
│   ├── enrich_reviews.py
│   ├── rag_chat.py
│   └── text_to_sql.py
│
├── airflow/
│   ├── dags/
│   │   └── zomato_batch.py
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── snowflake/
│   └── SQL scripts
│
├── zomato/
│   ├── models/
│   ├── macros/
│   ├── seeds/
│   └── dbt_project.yml
│
├── .gitignore
├── .env.example
├── profiles.yml.example
└── README.md
```

---

## ⚙️ Setup & Usage

### 1. Clone the Repository

```bash
git clone <your-repository-url>

cd zomato-ai-data-engineering
```

---

### 2. Configure Environment Variables

Create your environment configuration using the example file:

```bash
.env.example
```

Add the required credentials for services such as:

* AWS
* Snowflake
* Google Gemini

---

## ❄️ dbt

Navigate to the dbt project:

```bash
cd zomato
```

### Check the dbt Connection

```bash
dbt debug
```

### Build the dbt Models

```bash
dbt build
```

This builds the transformation pipeline and creates the required analytical models in Snowflake.

---

## 🤖 Run the AI Applications

### Review Enrichment

```bash
python ai/enrich_reviews.py
```

### RAG Review Assistant

```bash
streamlit run ai/rag_chat.py
```

### Text-to-SQL

```bash
streamlit run ai/text_to_sql.py
```

---



## 📊 What This Project Demonstrates

This project demonstrates an end-to-end modern data platform by combining:

### Data Engineering

* Cloud object storage with Amazon S3
* Data ingestion
* Snowflake data warehousing
* Layered warehouse architecture
* dbt transformations
* Fact and dimension modeling
* Analytical marts

### Data Pipeline & Orchestration

* Apache Airflow
* DAG-based workflow orchestration
* Dockerized environments
* Automated dbt execution

### Generative AI

* Google Gemini
* LLM-powered review enrichment
* Retrieval-Augmented Generation
* Semantic search
* Text-to-SQL
* Natural-language data exploration

### Applications

* Streamlit
* AI-powered review analysis
* Conversational data access

---

## 🎯 Project Goal

The goal of this project is to demonstrate how **cloud data engineering, modern data warehousing, pipeline orchestration, and Generative AI** can be combined into a single end-to-end analytics platform.

The project takes raw Zomato-style data and transforms it into:

```text
Raw Data
   ↓
Cloud Storage
   ↓
Data Warehouse
   ↓
Data Transformation
   ↓
Analytics-ready Data
   ↓
AI Applications
```

This showcases a practical workflow similar to the architecture used in modern **Data Engineering and AI-powered analytics platforms**.

---

## ⭐ Key Takeaways

By completing this project, the following concepts are demonstrated:

* ☁️ Cloud data storage
* ❄️ Cloud data warehousing
* 🔄 ETL/ELT pipelines
* 🧱 Dimensional data modeling
* 🔧 dbt transformations
* 🛠️ Airflow orchestration
* 🐳 Docker
* 🐍 Python data processing
* 🤖 Generative AI
* 🔎 Semantic search
* 📚 RAG
* 🧠 Text-to-SQL
* 📊 Analytics-ready data modeling
* 🚀 AI-powered data applications

---

## 👨‍💻 Project

**Zomato AI Data Engineering Project**

A portfolio project demonstrating an end-to-end **Data Engineering + Generative AI** workflow using modern cloud and open-source technologies.
