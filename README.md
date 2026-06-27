# SENTRY

A self-contained Python project to replicate a research experiment on meta-leakage in AI reasoning traces. SENTRY tests whether language models inadvertently reveal hidden instructions (like "don't say the word Paris") by stating things like "I shouldn't say...".

## Architecture

```mermaid
graph TD
    A[User Prompts] -->|prompts/| B(runner/generate_traces.py)
    B -->|Generate traces| C[(data/traces/)]
    C -->|Read traces| D(detector/run_detection.py)
    D -->|Check heuristics| E[detector/heuristics.py]
    D -->|Ask Judge LLM| F[detector/judge.py]
    E -.-> D
    F -.-> D
    D -->|Save Results| G[(data/results/detection_results.csv)]
    G -->|Visualize (Streamlit)| H(dashboard/app.py)
    G -->|Serve API (FastAPI)| I(backend/main.py)
    I -->|Consume API| J(frontend/)
```
