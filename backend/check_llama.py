import os
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if llama_cpp is installed
try:
    import llama_cpp
    print("✅ llama_cpp is installed")
except ImportError:
    print("❌ llama_cpp is not installed. Please install it with: pip install llama-cpp-python")
    sys.exit(1)

# Define model path
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "llama-2-7b-chat.Q4_K_M.gguf")

# Check if model file exists
if os.path.exists(MODEL_PATH):
    print(f"✅ Model file found at: {MODEL_PATH}")
    print(f"   File size: {os.path.getsize(MODEL_PATH) / (1024 * 1024):.2f} MB")
else:
    print(f"❌ Model file not found at: {MODEL_PATH}")
    sys.exit(1)

# Try to load the model
try:
    print("🔄 Loading model... (this may take a moment)")
    llm = llama_cpp.Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,
        n_gpu_layers=0,
        verbose=False
    )
    print("✅ Model loaded successfully!")
    
    print("\n✅ All checks passed! The local LLM should be working properly.")
except Exception as e:
    print(f"❌ Error loading or using the model: {str(e)}")
    sys.exit(1)
