import itertools
from dataclasses import dataclass
from typing import Any, Dict, List, Union


@dataclass
class GridConfig:
    """
    Defines a search grid for strategy parameters.
    Supports fixed lists of values or ranges.
    """

    strategy: str
    params: Dict[str, Union[List[Any], Dict[str, Any]]]  # Param name -> list of values OR range dict
    max_combinations: int = 1000

    def generate_combinations(self) -> List[Dict[str, Any]]:
        """
        Expand the grid into a list of concrete parameter dictionaries.
        """
        keys = sorted(self.params.keys())
        value_lists = []

        for k in keys:
            v = self.params[k]
            if isinstance(v, list):
                value_lists.append(v)
            elif isinstance(v, dict) and "start" in v and "end" in v and "step" in v:
                # Numeric Range
                start = v["start"]
                end = v["end"]
                step = v["step"]
                # Generate range, inclusive dependent on logic, usually standard range is exclusive at end
                # Let's make it inclusive for "end" if possible or just standard
                # Using numpy-like range logic or simple loop
                vals = []
                curr = start
                while curr <= end:
                    vals.append(curr)
                    curr += step
                    # floating point protection
                    if isinstance(step, float):
                        curr = round(curr, 10)
                value_lists.append(vals)
            else:
                raise ValueError(f"Invalid grid param definition for {k}: {v}")

        # Cartesian Product
        combos = []
        for values in itertools.product(*value_lists):
            combos.append(dict(zip(keys, values, strict=False)))

        if len(combos) > self.max_combinations:
            raise ValueError(f"Grid generates {len(combos)} combinations, exceeding limit of {self.max_combinations}")

        return combos
