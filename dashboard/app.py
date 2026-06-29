# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
from pathlib import Path
import json

st.set_page_config(page_title="SENTRY Dashboard", layout="wide")

st.title("SENTRY — Meta-Leak Detection Dashboard")

base_dir = Path(__file__).parent.parent
results_file = base_dir / "data" / "results" / "detection_results.csv"
index_file = base_dir / "data" / "traces" / "index.json"

if not results_file.exists():
    st.warning("No results found. Please run the generation and detection scripts first.")
    st.stop()

@st.cache_data
def load_data():
    df = pd.read_csv(results_file)
    
    # Load traces for raw_outputs
    with open(index_file, 'r') as f:
        index_data = json.load(f)
        
    traces_cache = {}
    for item in index_data:
        filepath = base_dir / item["filepath"]
        if filepath.exists():
            with open(filepath, 'r') as f:
                trace = json.load(f)
                key = f"{item['prompt_id']}_{item['model']}"
                traces_cache[key] = trace["raw_output"]
                
    df["raw_output"] = df.apply(lambda row: traces_cache.get(f"{row['prompt_id']}_{row['model']}", "N/A"), axis=1)
    
    # Determine clean rate
    df["is_clean"] = ~(df["heuristic_meta_leak"] | df["heuristic_content_leak"] | df["judge_meta_leak"] | df["judge_content_leak"])
    return df

df = load_data()

# Section 1: Summary Cards
st.header("Overall Summary")
col1, col2, col3, col4 = st.columns(4)

total_traces = len(df)
meta_leak_rate = df["heuristic_meta_leak"].mean()
content_leak_rate = df["heuristic_content_leak"].mean()
clean_rate = df["is_clean"].mean()

col1.metric("Total Traces", total_traces)
col2.metric("Meta-Leak Rate (Heuristic)", f"{meta_leak_rate:.1%}")
col3.metric("Content-Leak Rate (Heuristic)", f"{content_leak_rate:.1%}")
col4.metric("Clean Rate", f"{clean_rate:.1%}")

# Section 2: Meta-Leak Rate by Model
st.header("Meta-Leak Rate by Model")
model_stats = df.groupby("model")["heuristic_meta_leak"].mean().reset_index()
fig1 = px.bar(model_stats, x="model", y="heuristic_meta_leak", color="model", 
              labels={"heuristic_meta_leak": "Heuristic Meta-Leak Rate", "model": "Model"})
fig1.update_layout(yaxis_tickformat='.1%')
st.plotly_chart(fig1, use_container_width=True)

# Section 3: Meta-Leak Rate by Category
st.header("Meta-Leak Rate by Category")
category_stats = df.groupby("category")["heuristic_meta_leak"].mean().reset_index()
fig2 = px.bar(category_stats, x="category", y="heuristic_meta_leak", color="category",
              labels={"heuristic_meta_leak": "Heuristic Meta-Leak Rate", "category": "Category"})
fig2.update_layout(yaxis_tickformat='.1%')
st.plotly_chart(fig2, use_container_width=True)

# Section 4: Trace Browser
st.header("Trace Browser")

st.sidebar.header("Filters")
selected_models = st.sidebar.multiselect("Models", df["model"].unique(), default=df["model"].unique())
selected_categories = st.sidebar.multiselect("Categories", df["category"].unique(), default=df["category"].unique())
leak_type = st.sidebar.selectbox("Leak Type", ["All", "Meta-Leak", "Content-Leak", "Clean"])

filtered_df = df[df["model"].isin(selected_models) & df["category"].isin(selected_categories)]

if leak_type == "Meta-Leak":
    filtered_df = filtered_df[filtered_df["heuristic_meta_leak"] | filtered_df["judge_meta_leak"]]
elif leak_type == "Content-Leak":
    filtered_df = filtered_df[filtered_df["heuristic_content_leak"] | filtered_df["judge_content_leak"]]
elif leak_type == "Clean":
    filtered_df = filtered_df[filtered_df["is_clean"]]

st.write(f"Showing {len(filtered_df)} traces")

display_cols = ["prompt_id", "model", "category", "heuristic_meta_leak", "heuristic_content_leak", "judge_meta_leak", "judge_content_leak"]

for index, row in filtered_df.iterrows():
    expander_title = f"{row['prompt_id']} | {row['model']} | Meta-Leak: {row['heuristic_meta_leak']} | Content-Leak: {row['heuristic_content_leak']}"
    with st.expander(expander_title):
        st.markdown("**Heuristic Evidence:**")
        st.write(row["heuristic_evidence"] if row["heuristic_evidence"] else "None")
        
        st.markdown("**Judge Evidence:**")
        st.write(row["judge_evidence"] if row["judge_evidence"] else "None")
        
        st.markdown("**Raw Output:**")
        st.text(row["raw_output"])

csv_data = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Export Highlights",
    data=csv_data,
    file_name='sentry_highlights.csv',
    mime='text/csv',
)
