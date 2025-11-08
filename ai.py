import ollama

def analyze_errors(errors):
    prompt = "You are a DevOps SRE expert. Here are the top errors:\n"
    for e in errors[:5]:
        prompt += f"- {e['text']}\n"
    prompt += "\nWhat is the root cause? Give 1 short sentence."
    
    # CHANGED TO 1b MODEL
    response = ollama.generate(model='llama3.2:1b', prompt=prompt)
    return response['response']