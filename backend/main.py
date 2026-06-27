from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
from pathlib import Path

app = FastAPI(title="SENTRY API")

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = Path(__file__).parent.parent
results_file = base_dir / "data" / "results" / "detection_results.csv"
index_file = base_dir / "data" / "traces" / "index.json"

def load_data():
    if not results_file.exists():
        return pd.DataFrame(), []
        
    df = pd.read_csv(results_file)
    
    traces_cache = {}
    if index_file.exists():
        with open(index_file, 'r') as f:
            index_data = json.load(f)
            
        for item in index_data:
            filepath = base_dir / item["filepath"]
            if filepath.exists():
                with open(filepath, 'r') as f:
                    trace = json.load(f)
                    key = f"{item['prompt_id']}_{item['model']}"
                    traces_cache[key] = trace["raw_output"]
                    
    df["raw_output"] = df.apply(lambda row: traces_cache.get(f"{row['prompt_id']}_{row['model']}", "N/A"), axis=1)
    df["is_clean"] = ~(df["heuristic_meta_leak"] | df["heuristic_content_leak"] | df["judge_meta_leak"] | df["judge_content_leak"])
    
    return df, index_data

@app.get("/api/summary")
def get_summary():
    df, _ = load_data()
    if df.empty:
        return {"error": "No data available"}
        
    return {
        "total_traces": len(df),
        "meta_leak_rate": float(df["heuristic_meta_leak"].mean()),
        "content_leak_rate": float(df["heuristic_content_leak"].mean()),
        "clean_rate": float(df["is_clean"].mean())
    }

@app.get("/api/stats/models")
def get_model_stats():
    df, _ = load_data()
    if df.empty:
        return []
    
    stats = df.groupby("model")[["heuristic_meta_leak", "heuristic_content_leak", "judge_meta_leak"]].mean().reset_index()
    return stats.to_dict(orient="records")

@app.get("/api/stats/categories")
def get_category_stats():
    df, _ = load_data()
    if df.empty:
        return []
    
    stats = df.groupby("category")[["heuristic_meta_leak", "heuristic_content_leak", "judge_meta_leak"]].mean().reset_index()
    return stats.to_dict(orient="records")

@app.get("/api/traces")
def get_traces():
    df, _ = load_data()
    if df.empty:
        return []
        
    # Replace NaN with empty string to avoid JSON errors with nan
    df = df.fillna("")
    return df.to_dict(orient="records")
