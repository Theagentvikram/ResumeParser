#!/usr/bin/env python3
"""
Direct test of Mistral 7B Instruct model without going through the API.
This script will load the model directly and test it with a sample resume.
"""

import os
import json
from llama_cpp import Llama

# Test resume text
TEST_RESUME = """
John Doe
Software Engineer

EXPERIENCE:
Senior Software Engineer, ABC Tech (2018-Present)
- Developed and maintained cloud-based applications using Python and AWS
- Led a team of 5 developers on a major project

Software Developer, XYZ Solutions (2015-2018)
- Built web applications using React and Node.js
- Implemented CI/CD pipelines

EDUCATION:
Master of Computer Science, Stanford University (2015)
Bachelor of Engineering, MIT (2013)

SKILLS:
Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, CI/CD
"""

def main():
    print("🔍 Direct Mistral 7B Instruct Model Test 🔍")
    print("==========================================")
    
    # Path to the Mistral model
    model_path = os.path.join("backend", "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at: {model_path}")
        return False
    
    print(f"✅ Found model at: {model_path}")
    print("Loading model (this may take a moment)...")
    
    # Load the model
    llm = Llama(
        model_path=model_path,
        n_ctx=4096,           # Context size
        n_gpu_layers=0,       # CPU only
        verbose=False,
        n_threads=4,          # Use multiple threads
        n_batch=512           # Batch size
    )
    
    print("✅ Model loaded successfully")
    
    # Create a prompt for Mistral 7B Instruct
    prompt = f"""<s>[INST]Analyze this resume and extract key information as JSON:

```
{TEST_RESUME}
```

Extract: summary (1-2 sentences), skills (list), experience (years as number), educationLevel (highest degree), category (job field).[/INST]

```json
"""
    
    print("Generating response (this may take a moment)...")
    
    # Generate completion
    response = llm(
        prompt,
        max_tokens=512,
        temperature=0.1,
        top_p=0.95,
        stop=["</s>", "[/INST]"]
    )
    
    # Extract generated text
    generated_text = response["choices"][0]["text"] if "choices" in response else ""
    
    # Try to complete the JSON object if it was cut off
    if generated_text and not "}" in generated_text:
        generated_text += '}'
        
    # Make sure it starts with a proper JSON format
    if generated_text and not generated_text.startswith('{'):
        generated_text = '{' + generated_text
    
    print("\n--- Generated Response ---")
    print(generated_text)
    
    # Try to parse as JSON
    try:
        result = json.loads(generated_text)
        print("\n--- Parsed JSON Result ---")
        print(json.dumps(result, indent=2))
        return True
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse response as JSON: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n✅ Test completed successfully" if success else "\n❌ Test failed")
