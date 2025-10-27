# Autopool System High Level Overview

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-system-high-level-overview

---

The purpose of the Autopool System is to continuously rebalance assets into the Destinations with the best return/risk profile. Earnings are auto-compounded for the users, reinvested into the Autopool, and then rebalanced out to begin earning. We’ll give an overview of how things work by looking at how the assets flow through the system.
Step 1: Users deposit assets
Users must deposit assets into an Autopool for there to be assets to deploy. If this is a contract-to-contract interaction, this can happen directly in an Autopool. If this is a user interaction, through our UI, this will happen through our Router. The end-result is that the Autopool has idle assets sitting in it and the external party has Autopool shares in their wallet.
Step 2: Rebalance
Once a sufficient number of assets are deposited, the Autopool, or more importantly the Strategy backing the Autopool, will begin to accept rebalance proposals from our Solver. When a proposal satisfies the constraints of the Strategy:
The Autopools underlying asset, WETH in this case, will be sent to the Solver specified in the proposal
The Solver will take those underlying assets and turn them into the LP tokens for the Destination specified in the proposal. This can involve swaps, liquidity provisioning, or w/e other means the Solver has to procure the LP tokens.
The Solver will send those LP tokens back to the Autopool
Once validating everything looks good with the Strategy, the Autopool deposit those LP tokens into the corresponding DestinationVault for that Destination.
The DestinationVault will do what it needs to with the LP tokens depending on the type of Destination it is. If its just a pool Destination then the LP tokens can stay there. If its a Curve+Convex Destination, then the DestinationVault will stake the tokens into Convex.
The DestinationVault mints the Autopool 1:1 shares of itself to represent the deposit
Each DestinationVault has its own Rewarder where its shares are virtually staked on the Autopools behalf.
At the end of the rebalance, the Autopool has less of its base asset, and some number of DestinationVault shares representing a claim on some LP tokens.
Step 3: Auto-Compounding
On a periodic basis, rewards from the Destinations will claimed and collected via a permissioned keeper process. This is most-likely, though not restricted to, incentive tokens through say Convex or Aura, for example.
These tokens all go to a central LiquidationRow contract where they can be liquidated to the base asset in bulk at a later time.
When that liquidation occurs, assets are sent back proportionately to the DestinationVaults that contributed to their balance. These assets are held in the DestinationVaults Rewarder where the Autopools earn them over a short period of time.
Step 4: Debt Reporting
At least every 24 hours, each Autopool goes through a debt reporting where we re-value the LP tokens held by that Autopool. During that process, any available auto-compounded rewards are claimed and come into the Autopool as idle funds.
Step 5: Rinse and Repeat
With sufficient idle assets in the Autopool, another rebalance can occur. There is no requirement that funds earned from a Destination must go back to that Destination.
The above outline focused on idle → LP rebalances but the rebalance step can occur for LP → LP rebalances as well. So long as the proposal results in a higher potential return (and satisfies other constraints) it can be executed.
Previous
Autopool ETH Contracts Overview
Next
Autopool Contracts and Systems
Last updated
1 month ago
Was this helpful?