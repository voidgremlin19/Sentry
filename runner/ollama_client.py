import requests
import json

def generate(model: str, prompt: str, system: str | None = None) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    if system:
        payload["system"] = system

    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Ollama API error {response.status_code}: {response.text}")
        
    data = response.json()
    return data.get("response", "")

if __name__ == "__main__":
    models = ["llama3.2:1b", "qwen2.5:7b-instruct", "deepseek-r1:7b"]
    for model in models:
        try:
            print(f"Testing model {model}...")
            res = generate(model, "Say 'Hello, World!'")
            print(f"Success! Response: {res}\n")
        except Exception as e:
            print(f"Failed for {model}: {e}\n")
