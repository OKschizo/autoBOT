# Autopool Contracts Glossary

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-glossary

---

Autopool System
- Name of the overall system
Autopool
- A 4626 vault that users deposit assets into
AutoPoolETH
- A specific implementation of an AutoPool denominated in ETH/WETH
Destination
- An external contract, or set of contracts, that we LP/stake user funds into
Examples
A Balancer pool
A Balancer pool with LP staked into Aura
A Curve pool with LP staked into Convex
DestinationVault
- A contract that sits in front of a Destination in our system. These act has a proxy and give us a common interface to that Destination to perform our operations.
Solver
- Contract that can turn assets into LP tokens, LP tokens into other LP tokens, or LP tokens into assets
Strategy
- A contract that determines whether a Rebalance is in the best interest of an Autopool
Rebalance
- The deployment of:
Idle funds to a Destination
Funds from one Destination to another Destination
Funds from one Destination back to Idle
Liquidation -
The process of taking rewards and auto-compounding them into WETH
Previous
Autopools
Next
Contract Addresses
Last updated
1 month ago
Was this helpful?