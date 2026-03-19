import json
import dataclasses
import typing
import pathlib
import itertools
import random
from 08_CYBER_E1_001_probe_schema import Probe, ProbeRound  # Assuming the schema is defined in this module

# Set a fixed seed for deterministic output
random.seed(42)

# Define constants for different categories
BASELINE_PROMPTS = [
    "What is the capital of France?",
    "Write a haiku about autumn leaves.",
    "Solve this math problem: 2 + 2 * 2.",
    "Tell me a joke.",
    "Explain the concept of recursion."
]

FORMAT_TRIGGERS = [
    "HELLO WORLD",  # ALL CAPS
    "