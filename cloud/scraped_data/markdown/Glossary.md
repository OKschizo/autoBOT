# Glossary

Source: https://docs.auto.finance/auto-pools-protocol/glossary

---

Term
Definition
Autopool
An
ERC-4626
Tokenized Vault Standard pool within which user assets are deposited, which contains various different external destination contracts. Example destination contracts would be a Balancer or a Curve pool.
autoLP
Automated Liquidity Provision, used in reference to the network capabilities of assets deposited into Autopools and their corresponding yield bearing tokens
autoETH
autoETH is the yield-bearing Autopilot receipt token (also referred to as LAT) received after depositing ETH (or Wrapped ETH) into Autopilot's first Autopool, focused on LST-centric destinations.
autoLRT
autoLRT is a yield-bearing Autopilot receipt token for an LRT-based Autopool.
LP
Liquidity Provider, user who provides tokens as trading liquidity to exchanges. In the context of Autopilot, an LP is a participant that supplies ETH (or otherwise) to an Autopool.
Receipt Token
LPs receive receipt tokens (e.g., autoETH) upon deposit into an autopool. In essence, receipt tokens are tokenized automated liquidity networks backed by LP positions. They enable a new kind of composability within DeFi, as a standalone token representing optimally deployed underlying liquidity.
LST
Liquid staking tokens (LST) are tokenized ownership claims on the ETH staked on the Consensus layer, such as stETH or rETH.
LRT
A liquid restaking token (LRT) is a token that gives users access to liquidity while participating in restaking.
Rebalance Logic
Comprised of a series of smart contracts, the Rebalance Logic is the primary system of the Auto Pools Protocol that rebalances between a subset of given autopool destinations.
Solver
The Solver is an off-chain component that proposes rebalance solutions to interchangeably convert assets and LP tokens, as well as LP token into other LP tokens. The rebalance solutions are proposed to the Strategy, once they satisfy the Strategy’s imposed on-chain constraints a rebalance takes place.
Strategy
The Strategy contract is responsible for determining if a given liquidity rebalance is in the best interest of an autopool.
Rebalance
A deployment that occurs when: Idle assets move to a Destination, assets move from one Destination or another, or assets move from a Destination back to the idle state.
Destination
A liquidity pool within an autopool set that may be the destination venue of a potential asset rebalance.
Previous
Custom Autopools
Next
App Guide
Last updated
28 days ago
Was this helpful?