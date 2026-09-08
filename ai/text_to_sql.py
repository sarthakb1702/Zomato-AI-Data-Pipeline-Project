import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
from google import genai
import json
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-3.5-flash-lite"

FORBIDDEN_WORDS = ['drop', 'delete', 'truncate', 'alter', 'update', 'insert', 'create', 'replace', 'grant', 'revoke']

EXAMPLE_QUESTIONS = [
    "Top 10 cities by GMV",
    "Which cuisine has the most orders?",
    "Average delivery time by city, worst first",
    "Cancel rate by payment method"
]

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SCHEMA = """
Tables available (Snowflake). All tables are materialized in the MARTS schema. Use bare table names (e.g. FCT_ORDERS, never ZOMATO.MARTS.FCT_ORDERS).

DIM_CUSTOMER(
    customer_id,        -- NUMBER, unique customer identifier (Primary Key)
    customer_name,      -- VARCHAR, full name of customer
    email,              -- VARCHAR, lowercased email address
    age,                -- NUMBER, customer age in years
    age_segment,        -- VARCHAR, demographic group: 'Gen Z' (<25), 'Millennial' (25-39), 'Gen X' (40-54), 'Boomer' (55+), 'Unknown'
    gender,             -- VARCHAR, customer gender
    marital_status,     -- VARCHAR, marital status ('Single', 'Married', etc.)
    occupation,         -- VARCHAR, customer occupation ('Student', 'Employed', 'Self-Employed', etc.)
    income_band,        -- VARCHAR, monthly income bracket
    education,          -- VARCHAR, education qualification
    family_size         -- NUMBER, family size count
)
CRITICAL: DIM_CUSTOMER does NOT have any city or location column. NEVER query DIM_CUSTOMER.city!

DIM_DATE(
    date_day,           -- DATE, calendar date (Primary Key)
    year,               -- NUMBER, calendar year (e.g. 2024, 2025)
    month,              -- NUMBER, month number (1 to 12)
    month_name,         -- VARCHAR, month name ('Jan', 'Feb', etc.)
    day_name,           -- VARCHAR, day name ('Mon', 'Tue', etc.)
    is_weekend          -- BOOLEAN, TRUE for Saturday and Sunday, FALSE for weekdays
)

DIM_FOOD(
    f_id,               -- VARCHAR/NUMBER, unique food item identifier (Primary Key)
    food_name,          -- VARCHAR, item name (e.g. 'Veg Biryani', 'Butter Chicken')
    veg_or_non_veg      -- VARCHAR, dietary category ('Veg' or 'Non-Veg')
)

DIM_RESTAURANTS(
    restaurant_id,      -- NUMBER, unique restaurant identifier (Primary Key)
    restaurant_name,    -- VARCHAR, restaurant name
    city,               -- VARCHAR, city where the restaurant is located
    cuisine,            -- VARCHAR, primary cuisine type
    rating,             -- DECIMAL(3,1), average restaurant rating
    rating_count,       -- NUMBER, total count of ratings received
    cost_for_two        -- NUMBER, estimated cost for two in INR
)

FCT_ORDERS(
    order_id,           -- VARCHAR, unique order identifier (Primary Key)
    order_timestamp,    -- TIMESTAMP_NTZ, timestamp when the order was placed
    order_date,         -- DATE, date of the order
    customer_id,        -- NUMBER, foreign key referencing DIM_CUSTOMER.customer_id
    restaurant_id,      -- NUMBER, foreign key referencing DIM_RESTAURANTS.restaurant_id
    city,               -- VARCHAR, city where order occurred (derived from restaurant city)
    cuisine,            -- VARCHAR, cuisine category
    payment_method,     -- VARCHAR, payment mode (e.g. 'Credit Card', 'UPI', 'Cash on Delivery')
    order_status,       -- VARCHAR, order status: 'Delivered', 'Cancelled', 'Refunded'
    is_delivered,       -- BOOLEAN, TRUE if order_status = 'Delivered', else FALSE
    items_count,        -- NUMBER, count of distinct items in order
    sales_qty,          -- NUMBER, total quantity of items ordered
    subtotal,           -- DECIMAL, order subtotal before discounts, fees, taxes
    discount,           -- DECIMAL, discount amount
    delivery_fee,       -- DECIMAL, delivery fee
    gst,                -- DECIMAL, GST tax amount
    sales_amount,       -- DECIMAL, final billed amount for the order
    customer_rating,    -- NUMBER, order customer rating (1-5)
    delivery_time_min   -- NUMBER, delivery duration in minutes
)

FCT_ORDER_ITEMS(
    order_item_id,      -- VARCHAR, unique item line identifier (Primary Key)
    order_id,           -- VARCHAR, foreign key referencing FCT_ORDERS.order_id
    restaurant_id,      -- NUMBER, foreign key referencing DIM_RESTAURANTS.restaurant_id
    f_id,               -- VARCHAR/NUMBER, foreign key referencing DIM_FOOD.f_id
    order_ts,           -- TIMESTAMP_NTZ, timestamp when the order was placed
    order_date,         -- DATE, date of the order
    city,               -- VARCHAR, city of order / restaurant
    price,              -- DECIMAL(10,2), unit price of food item
    quantity,           -- NUMBER, item quantity ordered
    line_amount         -- DECIMAL(10,2), total line item amount (price * quantity)
)

MART_DAILY_CITY_REVENUE(
    order_date,         -- DATE, order date
    city,               -- VARCHAR, city of orders
    orders,             -- NUMBER, total orders placed: COUNT(*)
    delivered_orders,   -- NUMBER, successfully delivered orders: COUNT_IF(is_delivered)
    cancel_rate,        -- DECIMAL(6,4), cancellation rate: ROUND(DIV0(COUNT_IF(order_status='Cancelled'), COUNT(*)), 4)
    gmv,                -- DECIMAL, Gross Merchandise Value / Delivered Revenue: SUM(IFF(is_delivered, sales_amount, 0))
    aov                 -- DECIMAL(10,2), Average Order Value: ROUND(DIV0(gmv, delivered_orders), 2)
)

MART_DELIVERY_SLA(
    city,               -- VARCHAR, city of delivered orders
    order_hour,         -- NUMBER, hour of order timestamp (0 to 23)
    delivered_orders,   -- NUMBER, delivered orders count: COUNT_IF(is_delivered)
    p50,                -- DECIMAL(4,1), median (50th percentile) delivery time in minutes for delivered orders
    p90                 -- DECIMAL(4,1), 90th percentile delivery time in minutes for delivered orders
)

MART_RESTAURANT_PERFORMANCE(
    restaurant_id,      -- NUMBER, restaurant identifier
    restaurant_name,    -- VARCHAR, name of restaurant
    city,               -- VARCHAR, city where restaurant is located
    cuisine,            -- VARCHAR, primary cuisine
    orders,             -- NUMBER, total orders count: COUNT(*)
    revenue,            -- DECIMAL, delivered sales amount: SUM(IFF(is_delivered, sales_amount, 0))
    avg_customer_rating,-- DECIMAL(4,2), average customer rating: ROUND(AVG(customer_rating), 2)
    avg_delivery_min    -- DECIMAL(4,1), average delivery time in minutes: ROUND(AVG(delivery_time_min), 1)
)
"""

SYSTEM_PROMPT = f"""
You are a Snowflake SQL expert. Write ONE SELECT query that answers the question accurately based on the schema below.

CRITICAL RULES:
1. SELECT or WITH queries only. NEVER generate DDL or DML (no DROP, DELETE, ALTER, UPDATE, INSERT, CREATE, TRUNCATE, REPLACE).
2. Use bare table names ONLY (e.g. FCT_ORDERS, never ZOMATO.MARTS.FCT_ORDERS).
3. NEVER invent tables or columns. Only reference columns and tables explicitly declared in the schema below.
4. Add a LIMIT of 100 or less, unless the question asks for a single scalar aggregate/total.
5. Reply as JSON in this exact format: {{"sql": "your query here"}}

TABLE RELATIONSHIPS & JOINS:
- FCT_ORDERS.customer_id = DIM_CUSTOMER.customer_id
- FCT_ORDERS.restaurant_id = DIM_RESTAURANTS.restaurant_id
- FCT_ORDERS.order_date = DIM_DATE.date_day
- FCT_ORDER_ITEMS.order_id = FCT_ORDERS.order_id
- FCT_ORDER_ITEMS.restaurant_id = DIM_RESTAURANTS.restaurant_id
- FCT_ORDER_ITEMS.f_id = DIM_FOOD.f_id
- FCT_ORDER_ITEMS.order_date = DIM_DATE.date_day
- MART_RESTAURANT_PERFORMANCE.restaurant_id = DIM_RESTAURANTS.restaurant_id

CITY SEMANTICS:
- DIM_CUSTOMER has NO city column! Never reference DIM_CUSTOMER.city.
- Restaurant location: use DIM_RESTAURANTS.city or MART_RESTAURANT_PERFORMANCE.city.
- Order location: use FCT_ORDERS.city, FCT_ORDER_ITEMS.city, MART_DAILY_CITY_REVENUE.city, or MART_DELIVERY_SLA.city.
- Customer behavior by city (e.g. "customers who ordered in Pune", "top spending customers in Delhi"):
  JOIN DIM_CUSTOMER c JOIN FCT_ORDERS o ON c.customer_id = o.customer_id AND o.city = '<city_name>'.

METRIC & BUSINESS DEFINITIONS:
- GMV / Revenue means DELIVERED sales amount: SUM(IFF(is_delivered, sales_amount, 0)) or filter WHERE is_delivered = TRUE.
- Cancel Rate: COUNT_IF(order_status = 'Cancelled') / COUNT(*).
- AOV (Average Order Value): GMV / delivered_orders.
- Delivery Percentiles: In MART_DELIVERY_SLA, column names are 'p50' (median delivery min) and 'p90' (90th percentile). There is NO 'p50_delivery_min' or 'late_rate' column.

TABLE SELECTION GUIDELINES:
- Prefer existing MART tables when they directly answer the question:
  * MART_DAILY_CITY_REVENUE: for daily/city GMV, total orders, delivered orders, cancel rates, or AOV.
  * MART_RESTAURANT_PERFORMANCE: for restaurant-level revenue, order volume, average customer rating, or average delivery time. (Note: does NOT contain cancel_rate).
  * MART_DELIVERY_SLA: for hourly delivery percentiles (p50, p90) by city.
- Use FCT_ORDERS: for order-level analysis, payment method breakdowns, customer rating analysis, or custom date/time filters.
- Use FCT_ORDER_ITEMS joined with DIM_FOOD: for item-level dish sales, quantity sold, dish popularity, or veg vs non-veg dish breakdown.
- Use DIM_CUSTOMER: for customer demographic breakdowns (age_segment, gender, occupation, income_band, education, family_size).
- Use DIM_DATE: for calendar breakdowns (year, month, month_name, day_name, is_weekend).

{SCHEMA}
"""
 


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="MARTS",
        role = "DBT_ROLE"
    )


def generate_sql(question):
    response = client.models.generate_content(
        model=MODEL,
        contents=f"""
{SYSTEM_PROMPT}

User question:
{question}
""",
        config={
            "temperature": 0,
            "response_mime_type": "application/json"
        }
    )

    answer = response.text

    sql = json.loads(answer)["sql"]

    sql = sql.replace("ZOMATO.MARTS.", "").replace("ZOMATO.", "")

    return sql.strip().rstrip(";")


def is_safe(sql):
    lowered = sql.lower()

    if not lowered.startswith("select") and not lowered.startswith("with"):
        return False

    for word in FORBIDDEN_WORDS:
        if word in lowered:
            return False

    return True

def run_query(sql):
    conn = get_connection()
    cursor = conn.cursor()
    return cursor.execute(sql).fetch_pandas_all()


st.title("Chat with your Zomato Data")
st.caption(f"Ask in English, {MODEL} writes the SQL, Snowflake runs it")

with st.sidebar:
    st.header("Example Questions")
    for q in EXAMPLE_QUESTIONS:
        st.markdown(f" - {q}")

question = st.text_input("Enter your question here", 
                         placeholder="e.g. Top 10 restaurants by revenue in Bangalore")


if question:
    sql = generate_sql(question)
    st.code(sql, language="sql")

    if not is_safe(sql):
        st.error("The generated SQL is not safe to run. Please modify your question.")

    else:
        try:
            df = run_query(sql)
            st.success(f"{len(df)} rows returned")
            st.dataframe(df, hide_index=True)

            if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                st.bar_chart(df, x=df.columns[0], y=df.columns[1])

        except Exception as e:
            st.error(f"Error running query: {e}")