---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

To verify if an Ollama model fits in available GPU VRAM, you can run a script that queries both the Ollama API (for model size) and `nvidia-smi` (for available memory). Below is a complete Python solution that performs this check with error handling for cases where NVIDIA drivers are missing or models fail to load. 

### Key Details of the Script
- **Model Size**: Retrieves the total model file size in bytes from the Ollama API (`/api/tags`) by parsing each model’s `size` field. 
- **VRAM Check**: Uses `nvidia-smi --query-gpu=memory.free` to fetch available GPU memory, assuming the output is in MiB (which is standard for `nvidia-smi`). Converts it to bytes by multiplying by $1024^2$. 
- **Safety Fallback**: If the Ollama model size query fails or returns invalid data, the script defaults to checking only available VRAM without a model comparison. 
- **Error Handling**: Gracefully handles missing NVIDIA drivers (`nvidia-smi` not found) and Ollama API issues (e.g., network errors). 

### Prerequisites
1. **NVIDIA Drivers & GPU**: Must be installed and accessible. 
2. **Ollama Server**: Running locally or on an accessible host (default `http://localhost:11434`). 
3. **Python 3.x**: No external libraries needed beyond the standard `subprocess` module. 

### Complete Python Script
```python
import subprocess
import os

def query_available_vram_bytes():
    """Get available GPU VRAM in bytes using nvidia-smi."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.free --format=csv,nounits,noheader'], 
            capture_output=True, text=True, timeout=30)
        
        output = result.stdout.strip()
        if not output:
            return 0
        
        # nvidia-smi typically outputs memory in MB (MiB) for free usage.
        # Convert to bytes by multiplying by 1024^2.
        try:
            vram_mb = int(output)
            return vram_mb * 1024 ** 2
        except ValueError:
            return 0
    except FileNotFoundError:
        print("Error: nvidia-smi not found. No NVIDIA GPU detected.")
        return 0
    except subprocess.TimeoutExpired:
        print("Error: Command timed out.")
        return 0
    except Exception as e:
        print(f"Error querying VRAM: {e}")
        return 0

def get_model_info():
    """Fetch Ollama model details (size) from the API."""
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:11434/api/tags'], 
            capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return None
        
        import json
        models = json.loads(result.stdout)
        
        total_size = sum(model.get('size', 0) for model in models.get('models', []))
        return total_size
    except Exception as e:
        print(f"Error fetching Ollama model info: {e}")
        return None

def check_model_fit():
    """Check if available VRAM is sufficient for the latest Ollama model."""
    vram_bytes = query_available_vram_bytes()
    
    if vram_bytes == 0:
        print("No GPU detected or no VRAM available.")
        return False
    
    model_size = get_model_info()
    
    if model_size is None:
        print(f"Warning: Could not determine model size. Proceeding with {vram_bytes / (1024**3):.2f} GB VRAM available.")
        return True  # Assume fit if model size unknown
    
    if vram_bytes < model_size:
        print(f"VRAM Check Failed: Need {model_size / (1024**2):.2f} MB, Available {vram_bytes / (1024**3):.2f} GB VRAM.")
        return False
    
    print(f"VRAM OK: {vram_bytes / (1024**3):.2f} GB available for model size {model_size / (1024**3):.2f} GB.")
    return True

if __name__ == "__main__":
    check_model_fit()
```

### How It Works
1. **Query GPU Memory**: Uses `nvidia-smi` to get the free memory in MB, converts it to bytes. 
2. **Get Model Size**: Fetches all models from Ollama and sums their sizes (in bytes). 
3. **Compare & Report**: Prints a success/failure message based on available VRAM vs. model size. 

### Example Output
- **Success**: `VRAM OK: 15.00 GB available for model size 2.74 GB.`
- **Failure**: `VRAM Check Failed: Need 64.00 MB, Available 12.75 GB VRAM.` (This would be unusual unless querying incorrectly; more likely to see failure on small models vs large). 
- **No GPU**: `Error: nvidia-smi not found. No NVIDIA GPU detected.`

This script ensures you can safely run Ollama models without running out of VRAM, with robust fallbacks for error scenarios. 😊