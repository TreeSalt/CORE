---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

### Proposal for `activation_collector.py`

Below is a proposal for the `activation_collector.py` script that meets the specified requirements and constraints.

```python
import json
import dataclasses
import typing
import pathlib
import math
import statistics
import urllib.request
import time

# Define the ProxyActivations dataclass
@dataclasses.dataclass
class ProxyActivations:
    entropy: float
    word_entropy: float
    gen_speed: float

# Function to calculate character-level entropy
def collect_response_entropy(text: str) -> float:
    if not text:
        return 0.0
    
    frequency = {}
    for char in text:
        if char in frequency:
            frequency[char] += 1
        else:
            frequency[char] = 1
    
    total_chars = len(text)
    entropy = 0.0
    for count in frequency.values():
        probability = count / total_chars
        entropy -= probability * math.log2(probability)
    
    return entropy

# Function to calculate word-level entropy
def collect_word_entropy(text: str) -> float:
    if not text:
        return 0.0
    
    words = text.split()
    if not words:
        return 0.0
    
    word_frequency = {}
    for word in words:
        if word in word_frequency:
            word_frequency[word] += 1
        else:
            word_frequency[word] = 1
    
    total_words = len(words)
    word_entropy = 0.0
    for count in word_frequency.values():
        probability = count / total_words
        word_entropy -= probability * math.log2(probability)
    
    return word_entropy

# Function to calculate generation speed
def collect_generation_speed(response_obj: typing.Dict) -> float:
    if 'generated_at' not in response_obj or 'prompt_length' not in response_obj or 'response_length' not in response_obj:
        return 0.0
    
    generated_at = response_obj['generated_at']
    prompt_length = response_obj['prompt_length']
    response_length = response_obj['response_length']
    
    try:
        generation_time = time.time() - float(generated_at)
        if generation_time <= 0:
            return 0.0
        tokens_per_second = (response_length - prompt_length) / generation_time
        return tokens_per_second
    except (ValueError, TypeError):
        return 0.0

# Function to collect all proxy metrics
def collect_all_proxies(response: str, response_obj: typing.Dict) -> ProxyActivations:
    entropy = collect_response_entropy(response)
    word_entropy = collect_word_entropy(response)
    gen_speed = collect_generation_speed(response_obj)
    
    return ProxyActivations(entropy=entropy, word_entropy=word_entropy, gen_speed=gen_speed)

# Test the module
if __name__ == "__main__":
    # Example response and response_obj for testing
    test_response = "This is a test response."
    test_response_obj = {
        "generated_at": str(time.time() - 5),  # Simulate a generation time 5 seconds ago
        "prompt_length": 3,
        "response_length": 25
    }
    
    # Collect proxy metrics
    proxy_activations = collect_all_proxies(test_response, test_response_obj)
    
    # Assertions
    assert proxy_activations.entropy > 0, "Entropy should be non-zero"
    assert proxy_activations.word_entropy > 0, "Word entropy should be non-zero"
    assert proxy_activations.gen_speed > 0, "Generation speed should be positive"
    
    print("All tests passed successfully.")
```

### Explanation:
- **ProxyActivations Dataclass**: This dataclass holds the calculated proxy metrics for entropy, word entropy, and generation speed.
- **Entropy Calculation**: The `collect_response_entropy` function calculates the character-level entropy of the response text.
- **Word Entropy Calculation**: The `collect_word_entropy` function calculates the word-level entropy of the response text.
- **Generation Speed Calculation**: The `collect_generation_speed` function calculates the generation speed based on the time taken to generate the response.
- **Collect All Proxies**: The `collect_all_proxies` function collects all the proxy metrics into a `ProxyActivations` object.
- **Testing**: The script includes a test section that checks if the calculated metrics meet the specified criteria.

This script adheres to the constraints and requirements provided, ensuring it handles empty responses gracefully and does not write to any restricted directories.