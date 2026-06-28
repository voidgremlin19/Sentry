import json
import os
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detector.heuristics import check_heuristic
from detector.judge import judge_trace

def main():
    base_dir = Path(__file__).parent.parent
    traces_dir = base_dir / "data" / "traces"
    results_dir = base_dir / "data" / "results"
    
    index_file = traces_dir / "index.json"
    
    if not index_file.exists():
        print(f"Error: {index_file} not found. Run generate_traces.py first.")
        sys.exit(1)
        
    with open(index_file, 'r') as f:
        index_data = json.load(f)
        
    csv_path = results_dir / "detection_results.csv"
    
    # Load existing results to allow resuming
    results = []
    existing_keys = set()
    if csv_path.exists():
        try:
            df_existing = pd.read_csv(csv_path)
            results = df_existing.to_dict('records')
            for r in results:
                existing_keys.add(f"{r['prompt_id']}_{r['model']}")
            print(f"Loaded {len(results)} existing results. Resuming...")
        except Exception as e:
            print(f"Failed to load existing results: {e}")
    
    total = len(index_data)
    for i, item in enumerate(index_data):
        trace_key = f"{item['prompt_id']}_{item['model']}"
        if trace_key in existing_keys:
            print(f"[{i+1}/{total}] Skipping {item['prompt_id']} on {item['model']} (already evaluated)...")
            continue
            
        filepath = base_dir / item["filepath"]
        print(f"[{i+1}/{total}] Processing {item['prompt_id']} on {item['model']}...")
        
        try:
            with open(filepath, 'r') as f:
                trace = json.load(f)
                
            raw_output = trace["raw_output"]
            secret = trace["secret"]
            
            heuristic_res = check_heuristic(raw_output, secret)
            judge_res = judge_trace(raw_output, secret)
            
            new_result = {
                "prompt_id": trace["prompt_id"],
                "model": trace["model"],
                "category": trace["category"],
                "secret": trace["secret"],
                "heuristic_meta_leak": heuristic_res["meta_leak"],
                "heuristic_content_leak": heuristic_res["content_leak"],
                "heuristic_evidence": heuristic_res["evidence"],
                "judge_meta_leak": judge_res["meta_leak"],
                "judge_content_leak": judge_res["content_leak"],
                "judge_confidence": judge_res["confidence"],
                "judge_evidence": judge_res["evidence"]
            }
            results.append(new_result)
            
            # Incrementally save to CSV after each evaluation
            pd.DataFrame(results).to_csv(csv_path, index=False)
            
        except Exception as e:
            print(f"Failed processing {filepath}: {e}")
            
    df = pd.DataFrame(results)
    
    print(f"\nFinal results saved to {csv_path}\n")
    
    # Compute stats
    print("=== SUMMARY STATS ===")
    if not df.empty:
        print("\nMeta-leak rate per model (Heuristic):")
        print(df.groupby("model")["heuristic_meta_leak"].mean().apply(lambda x: f"{x:.1%}").to_string())
        
        print("\nMeta-leak rate per model (Judge):")
        print(df.groupby("model")["judge_meta_leak"].mean().apply(lambda x: f"{x:.1%}").to_string())
        
        print("\nContent-leak rate per model (Heuristic):")
        print(df.groupby("model")["heuristic_content_leak"].mean().apply(lambda x: f"{x:.1%}").to_string())
        
        print("\nMeta-leak rate per category (Heuristic):")
        print(df.groupby("category")["heuristic_meta_leak"].mean().apply(lambda x: f"{x:.1%}").to_string())
        
        agreement = (df["heuristic_meta_leak"] == df["judge_meta_leak"]).mean()
        print(f"\nAgreement between heuristic and judge for meta-leak: {agreement:.1%}")
    else:
        print("No data available.")

if __name__ == "__main__":
    main()
