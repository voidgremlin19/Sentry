# SENTRY

A self-contained Python project to replicate a research experiment on meta-leakage in AI reasoning traces. SENTRY tests whether language models inadvertently reveal hidden instructions (like "don't say the word Paris") by stating things like "I shouldn't say...".

## Architecture

```mermaid
graph TD
    A[User Prompts] -->|prompts/| B[runner/generate_traces.py]
    B -->|Generate traces| C[(data/traces/)]
    C -->|Read traces| D[detector/run_detection.py]
    D -->|Check heuristics| E[detector/heuristics.py]
    D -->|Ask Judge LLM| F[detector/judge.py]
    E -.-> D
    F -.-> D
    D -->|Save Results| G[(data/results/detection_results.csv)]
    G -->|Visualize in Streamlit| H[dashboard/app.py]
    G -->|Serve FastAPI| I[backend/main.py]
    I -->|Consume API| J[frontend/]
```

## Quick Start

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Pull the required Ollama models:
   ```bash
   ollama pull llama3.2:1b
   ollama pull qwen2.5:7b-instruct
   ollama pull deepseek-r1:7b
   ```

3. Generate the traces (this will run 40 prompts across 3 models):
   ```bash
   python runner/generate_traces.py
   ```

4. Run the detection (regex heuristics + LLM-as-judge):
   ```bash
   python detector/run_detection.py
   ```

5. Launch the visualization dashboard. You can use either the original Streamlit app or the new web app (FastAPI + Vite).

   **Option A: Streamlit Dashboard**
   ```bash
   streamlit run dashboard/app.py
   ```

   **Option B: Web App (FastAPI + Vite)**
   First, start the backend API:
   ```bash
   uvicorn backend.main:app --reload
   ```
   Then, in a separate terminal, start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Results

Based on the dashboard results across our local model runs, we observed the following:

### Meta-Leak Rate by Model
![Meta-Leak Rate by Model](assets/meta_leak_rate.png)
- **mistral:latest**: ~40% (Highest leakage rate)
- **gemma3:4b**: ~20%
- **llama3.2:3b**: ~20%
- **qwen3:4b**: ~20%

### Content-Leak Rate by Category
![Content-Leak Rate by Category](assets/content_leak_rate.png)
- **Addition**: ~50%
- **Suppression**: ~25%
- **Stylistic**: ~0%

### Examples of Leakage
- **Suppression Leaks**: Models instructed to suppress certain words often leaked the hidden instructions in their reasoning traces. 
  - For example, in trace `supp_01`, the model explicitly leaked the suppressed target word by reasoning: *"to simply say that the capital city of France is Paris..."*
  ![Trace supp_01](assets/trace_supp_01.png)
  - In trace `supp_03`, the LLM judge successfully detected a semantic leak regarding a specific shade (*"It's typically perceived as a shade of cerulean"*), even when simple heuristic matching failed.
  ![Trace supp_03](assets/trace_supp_03.png)

## Limitations

- Single run per prompt (no variance measured).
- Heuristic tier is keyword-based and may have false negatives.
- LLM judge is from a similar model family (qwen), which might introduce bias.
- This is a qualitative spot-check, not a fully controlled replication of parameter-count claims.
