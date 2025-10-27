# Destination Vaults

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/destination-vaults

---

Destination Vaults act as our proxy to the greater DeFi ecosystem. Their goal is to provide a common interface for us to deposit/withdraw LP tokens and earn yield. Each type of Destination has its own unique concrete DestinationVault implementation. Currently we support:
Balancer Pools
Balancer Pools with LP staked into Aura
Curve Pools with LP staked into Convex
Maverick Boosted Positions
Core Functionality
Depositing and Withdrawing LP Tokens
Autopool’s will be the main actors interacting with a Destination Vault. Primarily this will come in the form of deposit and withdrawing LP tokens. The actions taken after a deposit aren’t much of a concern to the Autopool and can vary depending on the specific type of Destination. If this is a just a “Balancer Pool” type of Destination then the LP tokens will stay in the Destination Vault. If this is a Destination that say stakes into Aura, then that operation will happen upon deposit.
Withdrawing can come in two forms: as the LP units, or as the base asset. The LP unit can be withdrawn as part of a rebalance. During a user withdraw where we have to pull from the market, the LP units burned and the resulting tokens will be swapped into the base asset. All base assets in the system will be WETH at this time. Additional validations will be required to support additional base assets.
Collecting Rewards
Depending on the type of Destination Vault, rewards may be due to us for holding or staking the LP units. The implementation of this can be hard coded to return nothing, or to interact with an external protocol. Resulting claimed tokens are sent to the caller of
collectRewards()
.
Marketplace Rewards
These functions are intentionally left empty at this time.
Architecture
Previous
Liquidation
Next
Autopools
Last updated
3 months ago
Was this helpful?