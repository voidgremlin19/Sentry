import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to allow importing from runner
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from runner.ollama_client import generate

def load_prompts(filepath: str) -> list:
    with open(filepath, 'r') as f:
        data = json.load(f)
    if isinstance(data, dict) and "prompts" in data:
        return data["prompts"]
    return data

def main():
    base_dir = Path(__file__).parent.parent
    prompts_file = base_dir / "prompts" / "attack_suite.json"
    traces_dir = base_dir / "data" / "traces"
    
    if not prompts_file.exists():
        print(f"Error: {prompts_file} not found.")
        sys.exit(1)
        
    prompts = load_prompts(str(prompts_file))
    models = ["mistral:latest", "qwen3:4b", "gemma3:4b", "llama3.2:3b"]
    
    index_file = traces_dir / "index.json"
    index_data = []
    if index_file.exists():
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
        except Exception:
            pass
    total_runs = len(prompts) * len(models)
    current_run = 0
    
    for prompt in prompts:
        prompt_id = prompt["id"]
        category = prompt["category"]
        secret = prompt["secret"]
        system_prompt = prompt["system"]
        user_query = prompt["user"]
        
        for model in models:
            current_run += 1
            print(f"[{current_run}/{total_runs}] Generating trace for prompt {prompt_id} on {model}...")
            
            try:
                response = generate(model, user_query, system_prompt)
                
                trace_data = {
                    "prompt_id": prompt_id,
                    "model": model,
                    "category": category,
                    "secret": secret,
                    "raw_output": response,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                safe_model_name = model.replace(":", "_")
                filename = f"{prompt_id}_{safe_model_name}.json"
                filepath = traces_dir / filename
                
                with open(filepath, 'w') as f:
                    json.dump(trace_data, f, indent=2)
                    
                index_data.append({
                    "prompt_id": prompt_id,
                    "model": model,
                    "category": category,
                    "filepath": str(filepath.relative_to(base_dir))
                })
                
            except Exception as e:
                print(f"Failed generation for {prompt_id} on {model}: {e}")
                
    index_file = traces_dir / "index.json"
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
        
    print("Generation complete.")

if __name__ == "__main__":
    main()
