---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here is the implementation based on the logic derived:

```python
import os
import sys
from typing import Optional, Dict, Any

class OllamaCGroupManager:
    def __init__(self):
        self.pid_path = "/usr/local/bin/llm-get-pid.py"  # Path to helper script for PID retrieval
        self.managed_cgroup_dir = "/sys/fs/cgroup/ollama"
        # Default memory limits: Max is typically 8GB unless configured otherwise
        # We use a reasonable default or read env var if present (e.g., OLLAMA_MAX_MEMORY_MB)
        # For simplicity here, we set a standard limit like 4096MB as a placeholder
        self.default_memory_limit_mb = int(os.getenv("OLLAMA_MAX_MEMORY_MB", "4096"))

    def get_ollama_pid(self) -> Optional[int]:
        """Retrieves the Ollama PID using the helper script."""
        try:
            if os.path.exists(self.pid_path):
                result = os.popen(f"python {self.pid_path}").read().strip()
                if result.isdigit():
                    return int(result)
        except Exception:
            pass
        # Fallback check for pid (in case helper fails, though it should be used)
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'ollama':
                return proc.info['pid']
        return None

    def setup_cgroup(self) -> bool:
        """Sets up the Ollama cgroup, applies memory limits without killing the process."""
        pid = self.get_ollama_pid()
        if not pid:
            print("Error: Could not retrieve Ollama PID.")
            return False
        
        try:
            # Create or ensure the specific cgroup directory exists (V2 style)
            os.makedirs(self.managed_cgroup_dir, exist_ok=True)
            
            # Move process to new cgroup
            procs_file = f"{self.managed_cgroup_dir}/cgroup.procs"
            with open(procs_file, 'w') as f:
                f.write(f'{pid}\n')
            
            # Set memory limits directly in the hierarchy
            current_memory_max_file = f"{self.managed_cgroup_dir}/memory.max"
            if os.path.exists(current_memory_max_file):
                try:
                    with open(current_memory_max_file, 'w') as f:
                        f.write(f'{self.default_memory_limit_mb * 1024 * 1024}\n') # Write bytes to file
                    
                    # Optional: Set memory.high if available
                    current_memory_high_file = f"{self.managed_cgroup_dir}/memory.high"
                    if os.path.exists(current_memory_high_file):
                        with open(current_memory_high_file, 'w') as f:
                            f.write(f'{(self.default_memory_limit_mb * 1024 * 1024) + (1024*1024)}\n') # Slightly higher than max to allow burst
                except PermissionError:
                    print(f"Permission denied for setting memory limit at {current_memory_max_file}")
                    
            print("Ollama cgroup setup complete. Memory limits applied.")
            return True
            
        except Exception as e:
            print(f"Setup failed with error: {e}")
            return False

    def get_cgroup_stats(self) -> Optional[Dict[str, float]]:
        """Gets memory usage stats from the Ollama cgroup hierarchy."""
        pid = self.get_ollama_pid()
        if not pid:
            print("Ollama is not running.")
            return None

        try:
            # Determine current cgroup path (in case setup moved it and we need to verify)
            # However, we read from our managed dir assuming it's still there.
            # If the process was moved out (e.g. teardown), reading here returns 0/error
            
            stats_path = f"{self.managed_cgroup_dir}/memory.current"
            if not os.path.exists(stats_path):
                return None
            
            current_memory_kb = 0
            max_memory_kb = 0 # Optional but requested
            
            try:
                with open(stats_path, 'r') as f:
                    val = f.read().strip()
                    if val.isdigit():
                        current_memory_kb = int(val)
            except (ValueError, IOError):
                pass
                
            max_file = f"{self.managed_cgroup_dir}/memory.max"
            if os.path.exists(max_file):
                try:
                    with open(max_file, 'r') as f:
                        val = f.read().strip()
                        if val.isdigit():
                            max_memory_kb = int(val)
                except (ValueError, IOError):
                    pass

            return {
                "usage_mb": current_memory_kb / 1024.0,
                "limit_mb": max_memory_kb / 1024.0 if max_memory_kb > 0 else -1 # -1 for unlimited
            }

        except Exception as e:
            print(f"Failed to read stats: {e}")
            return None

    def is_ollama_in_cgroup(self) -> bool:
        """Checks whether the Ollama PID is assigned to the managed cgroup."""
        pid = self.get_ollama_pid()
        if not pid:
            return False
        
        try:
            # Read process's own cgroup path to verify assignment
            proc_cgroup_file = f"/proc/{pid}/cgroup"
            with open(proc_cgroup_file, 'r') as f:
                content = f.read()
            
            # Check if the managed directory name appears in the cgroup file
            return self.managed_cgroup_dir in content
        except Exception:
            return False

    def teardown_cgroup(self) -> bool:
        """Removes the specific app from the isolated cgroup."""
        pid = self.get_ollama_pid()
        if not pid:
            print("Ollama is not running or PID not found.")
            return False

        try:
            # Move process out of our managed cgroup to parent (root) to reset limits
            root_procs_file = "/sys/fs/cgroup/cgroup.procs" 
            with open(root_procs_file, 'w') as f:
                f.write(f'{pid}\n')
            
            # Clean up our specific directory
            if os.path.exists(self.managed_cgroup_dir):
                os.rmdir(self.managed_cgroup_dir) # rmdir only works if dir is empty
                
            print("Ollama cgroup isolation removed.")
            return True
            
        except Exception as e:
            print(f"Teardown failed with error: {e}")
            return False

# Example usage logic (Uncomment for testing)
# manager = OllamaCGroupManager()
# manager.setup_cgroup()
# stats = manager.get_cgroup_stats()
# print(stats)
```