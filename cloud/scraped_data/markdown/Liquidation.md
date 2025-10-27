# Liquidation

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/liquidation

---

Liquidation in Autopilot refers to the process of auto-compounding rewards from our various asset deployments. For efficiency reasons, LiquidationRow attempts to batch as much of the claiming and swapping process as possible. This is broken up into two processes:
Claiming
Each DestinationVault is required to implement a
collectRewards()
function which will claim and transfer any reward tokens back to the liquidator. The exact details of how a claim happen are not of a concern to the liquidator, it is only worried about being told how much of some token it has received. Call flow:
Liquidation
Both the process of claiming and liquidation can be gas intensive given how many DestinationVaults and reward tokens we may need to process in the system. Both of these processes are designed to be able to work on a subset of either the DestinationVaults or the tokens to combat this. The goal is batch as match of the work as possible for efficiency, though. So, during liquidation the balance of tokens across many DestinationVaults are compiled, swapped as a single operation, and the proceeds distributed back to the DestinationVaults according to the share they contributed. Call flow:
Fees
This process is one that is permissioned and run by Tokemak. To support the gas and fees required to perform this a fee can optionally be enabled against any liquidated funds.
Previous
Autopool Router
Next
Destination Vaults
Was this helpful?