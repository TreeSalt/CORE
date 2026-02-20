# Performance Standards (Big O)

## 1. Core Mandate: O(N) or Better
All core path components in `antigravity_harness` MUST adhere to **O(N)** or **O(1)** time complexity.
- **O(1)**: Constant time (Hash map lookups, index access).
- **O(N)**: Linear time (Single pass data processing, vectorized operations).
- **O(N log N)**: Log-linear time (Sorting) is acceptable but must be justified.
- **O(N^2)**: Quadratic time (Nested loops over data frames) is **STRICTLY FORBIDDEN** in the critical path (simulation, signal generation, gap analysis).

## 2. Forbidden Patterns
### 2.1. `DataFrame.iterrows()`
Using `iterrows()` is a performance anti-pattern that converts optimized C-structs into heavy Python objects for every row.
**Status**: ⛔ BANNED in hot paths.
**Replacement**:
- **Vectorization**: Use Pandas/NumPy array operations (e.g., `df['a'] * df['b']`).
- **`itertuples()`**: If iteration is unavoidable, use `itertuples()` which is significantly faster (O(N) with lower constant factor).
- **List Comprehension**: `[func(x) for x in df['col']]` is often faster than row iteration.

### 2.2. Dynamic List Growth inside Loops
**Status**: ⚠️ DISCOURAGED for large N.
**Replacement**: Pre-allocate arrays/lists if size is known.

## 3. Vectorization Guide
### Slippage / Latency Calculation
**Bad (O(N) Python Overhead):**
```python
for idx, row in df.iterrows():
    df.at[idx, 'slippage'] = (row['fill'] - row['expected']) ...
```

**Good (O(N) C-Optimized):**
```python
df['slippage'] = (df['fill'] - df['expected']) ...
```

## 4. Enforcement
- Code reviews must flag `iterrows`.
- Performance degradation in `make all` benchmarks is grounds for rejection.
