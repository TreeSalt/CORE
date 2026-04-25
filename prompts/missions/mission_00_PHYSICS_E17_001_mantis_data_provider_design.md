# MISSION: mantis_data_provider_abstraction_design
TYPE: ARCHITECTURE
DELIVERABLE: docs/architecture/MANTIS_DATA_PROVIDER.md

Specify an abstract data provider interface with implementations for
Alpaca, IBKR, Binance, and generic CSV. Use dependency injection so
the pipeline doesn't import from any specific provider at module level.
Cover: connection lifecycle, error handling, retry policy, rate limiting,
historical replay capability.
