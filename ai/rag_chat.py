import os

import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector

from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

# Local FREE embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Gemini is used ONLY for generating the final answer
CHAT_MODEL = "gemini-3.5-flash-lite"

# Number of reviews to retrieve from Snowflake
NEW_REVIEWS = 500

# Number of relevant reviews given to Gemini
TOP_K = 5

# Local cache file for embeddings
CACHE_FILE = "review_embeddings.parquet"


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ============================================================
# LOCAL EMBEDDING MODEL
# ============================================================

@st.cache_resource
def load_embedding_model():
    """
    Load the Sentence Transformer model once.

    This model runs locally on your computer.
    It does NOT use Gemini API embedding requests.
    """

    return SentenceTransformer(EMBEDDING_MODEL)


embedding_model = load_embedding_model()


# ============================================================
# READ REVIEWS FROM SNOWFLAKE
# ============================================================

def read_reviews_from_snowflake():

    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )

    query = f"""
        SELECT
            REVIEW_ID,
            CITY,
            RATING,
            COMMENT
        FROM ZOMATO.STAGING.STG_REVIEWS
        SAMPLE ({NEW_REVIEWS} ROWS)
    """

    cursor = conn.cursor()

    try:
        df = cursor.execute(query).fetch_pandas_all()

    finally:
        cursor.close()
        conn.close()

    # Snowflake returns uppercase column names
    # Convert them to lowercase for easier Python usage
    df.columns = [col.lower() for col in df.columns]

    return df


# ============================================================
# CREATE LOCAL EMBEDDINGS
# ============================================================

def embed(texts):

    # Replace NULL/NaN values with empty strings
    cleaned_texts = []

    for text in texts:

        if pd.isna(text):
            text = ""

        cleaned_texts.append(str(text))

    # Generate embeddings locally
    embeddings = embedding_model.encode(
        cleaned_texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return embeddings.tolist()


# ============================================================
# LOAD REVIEWS + EMBEDDINGS
# ============================================================

@st.cache_data
def load_reviews():

    # If embeddings already exist, use the cached version
    if os.path.exists(CACHE_FILE):

        st.info("Loading reviews and embeddings from local cache...")

        return pd.read_parquet(CACHE_FILE)

    # Otherwise get reviews from Snowflake
    st.info("Loading reviews from Snowflake...")

    df = read_reviews_from_snowflake()

    # Create embeddings locally
    st.info("Creating local embeddings...")

    df["embedding"] = embed(
        df["comment"].tolist()
    )

    # Save embeddings locally
    df.to_parquet(CACHE_FILE)

    st.success("Embeddings created and cached locally.")

    return df


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(vec_a, vec_b):

    vec_a = np.array(vec_a)
    vec_b = np.array(vec_b)

    denominator = (
        np.linalg.norm(vec_a)
        * np.linalg.norm(vec_b)
    )

    if denominator == 0:
        return 0

    return np.dot(vec_a, vec_b) / denominator


# ============================================================
# FIND SIMILAR REVIEWS
# ============================================================

def find_similar_reviews(question, df):

    # Create embedding for the user's question
    question_vector = embed([question])[0]

    scores = []

    # Compare question embedding with every review embedding
    for review_vector in df["embedding"]:

        score = cosine_similarity(
            question_vector,
            review_vector
        )

        scores.append(score)

    # Make a copy so we don't modify the original dataframe
    result_df = df.copy()

    result_df["score"] = scores

    # Get the TOP_K most similar reviews
    top_reviews = result_df.nlargest(
        TOP_K,
        "score"
    )

    return top_reviews


# ============================================================
# ASK GEMINI
# ============================================================

def ask_llm(question, top_reviews):

    context = ""

    for _, row in top_reviews.iterrows():

        context += (
            f"City: {row['city']}\n"
            f"Rating: {row['rating']} stars\n"
            f"Review: {row['comment']}\n\n"
        )

    user_prompt = f"""
You are answering questions about Zomato customer reviews.

IMPORTANT RULES:

- Answer ONLY using the customer reviews provided below.
- Do not use outside knowledge.
- Do not invent information.
- Be concise and clear.
- If the provided reviews do not contain enough information
  to answer the question, say:

"The provided reviews do not contain enough information
to answer this question."

Question:
{question}

Customer Reviews:
{context}
"""

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=user_prompt
    )

    return response.text


# ============================================================
# STREAMLIT USER INTERFACE
# ============================================================

st.set_page_config(
    page_title="Zomato Review RAG",
    page_icon="🍽️",
    layout="wide"
)


st.title("🍽️ Chat with your Zomato Reviews")

st.caption(
    f"Searching {NEW_REVIEWS} reviews using "
    f"{EMBEDDING_MODEL}. "
    f"Answers generated using {CHAT_MODEL}."
)


# ============================================================
# LOAD DATA
# ============================================================

review_df = load_reviews()


# Display basic information
st.write(
    f"📊 Reviews available for search: **{len(review_df)}**"
)


# ============================================================
# USER QUESTION
# ============================================================

question = st.text_input(
    "Ask a question about your reviews:",
    placeholder=(
        "e.g. What are the most common complaints "
        "about delivery?"
    )
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    with st.spinner("Searching reviews..."):

        # Find the most relevant reviews
        top_reviews = find_similar_reviews(
            question,
            review_df
        )

    with st.spinner("Generating answer..."):

        # Give relevant reviews to Gemini
        answer = ask_llm(
            question,
            top_reviews
        )

    # ========================================================
    # DISPLAY ANSWER
    # ========================================================

    st.markdown("### 🤖 Answer")

    st.write(answer)


    # ========================================================
    # DISPLAY RETRIEVED REVIEWS
    # ========================================================

    with st.expander(
        "🔎 Reviews used to build this answer"
    ):

        display_df = top_reviews[
            [
                "city",
                "rating",
                "comment",
                "score"
            ]
        ].copy()

        display_df["score"] = display_df["score"].round(4)

        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True
        )