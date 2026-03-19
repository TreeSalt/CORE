import json
import urllib.request

def _get_ollama_status():
    """
    Fetches model status from Ollama API and formats for display.
    Returns a list of dictionaries with model details or an error message.
    """
    try:
        url = "http://localhost:11434/api/ps"
        # Timeout set to avoid hanging if Ollama isn't running
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        models = data.get("models", [])
        
        if not models:
            return [{"type": "status", "message": "No models loaded"}]
            
        formatted_status = []
        for model in models:
            name = model.get("name", "Unknown")
            size = model.get("size", 0)
            vram = model.get("size_vram", 0)
            
            # Avoid division by zero
            if size == 0:
                gpu_pct = "N/A"
            else:
                gpu_pct = f"{(vram / size) * 100:.2f}%"
                
            formatted_status.append({
                "type": "model_info",
                "name": name,
                "size_gb": round(size / (1024**3), 2),
                "gpu_pct": gpu_pct
            })

        return formatted_status
        
    except Exception as e:
        # Log error details if this was integrated into a logger
        # Return error dict consistent with caller expectations
        return [{"type": "error", "value": f"Ollama connection failed: {str(e)}"}]
