from typing import NewType

# The Physics of Money
Price = NewType("Price", float)
Quantity = NewType("Quantity", float)
Money = NewType("Money", float)
Fraction = NewType("Fraction", float)  # 0.0 to 1.0 (usually)

# Semantic Aliases
Seconds = NewType("Seconds", float)
UnixTimestamp = NewType("UnixTimestamp", float)
