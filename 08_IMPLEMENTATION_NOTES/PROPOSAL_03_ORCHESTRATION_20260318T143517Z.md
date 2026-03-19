---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
        try:
            req = urllib.request.Request("http://localhost:11434/api/ps", timeout=5)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if 'models' in data and len(data['models']) > 0:
                lines = []
                for model in data['models']:
                    name = model.get('name', 'Unknown')
                    size_bytes = model.get('size', 0)
                    vram_bytes = model.get('size_vram', 0)
                    
                    if size_bytes > 0:
                        gpu_pct = (vram_bytes / size_bytes) * 100
                        size_gb = round(size_bytes / (1024**3), 2)
                        lines.append(f"• {name} | Size: {size_gb:.2f} GB | GPU: {gpu_pct:.1f}%")
                    else:
                        lines.append(f"• {name} | CPU Only")
                
                return "\n".join(lines) + "\n"
            else:
                return "No models loaded\n"
        except Exception:
            return f"\033[91mOllama not responding\033[0m"
```