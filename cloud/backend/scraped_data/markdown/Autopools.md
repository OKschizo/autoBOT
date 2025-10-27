# Autopools

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/autopools

---

Autopools will be the main jumping off point for end-user interactions with the system (though technically this is the Router, these are the tokens the user will get back). Users will deposit and withdraw the base asset from here. Vaults are ERC 4626 + Permit compatible.
An Autopool is actually a pair of contracts. These contracts are:
The pool itself
A Convex-like, block height+rate style, Rewarder
The purpose of an Autopool is to represent a set of destinations that deposited assets may be deployed. It acts almost as an index. If an Autopool points to 5 destinations then your assets may be deployed to one or all of those destinations depending on how much those destinations are currently earning.
Base Asset
An Autopool should track it’s “base asset”. This is the asset that will be deposited and withdrawn from the pool. Any auto-compounding that happens will be in terms of the base asset, as well. However, it is expected that the Autopools associated Rewarder can emit any token(s).
Tracked Tokens
Autopools support being able to recover tokens that are erroneously sent to it. However, we would not want the ability to be able to transfer out any tokens that are core to operation of the Autopool. This would include the base asset and any DestinationVault shares that it currently holds. Tokens that should not be transferred are called “tracked”.
Debt Reporting
At least every 24 hours, or whenever valuations deviate by a certain threshold, the value of the DestinationVault tokens that are held by the Autopool are re-valued. Deposits and withdraws from the Autopool are based on these cached values. Should this debt reporting result in an increase in value, shares will be minted to the Autopool to offset the increase. This is to ensure there isn’t a sharp increase in the nav/share of Autopool. Auto-compounded rewards are also incorporated during this time.
Fees
Two types of fees can be taken by the Autopool and they are taken during Debt Reporting.
Periodic Fee - This is a set fee annualized fee that is taken each Debt Reporting
Streaming Fee - This fee is taken on profit earned by the Autopool. Optionally, this fee can only be taken when profit exceeds previous values (the high watermark).
Should the high watermark be enabled and not be broken for a period of 60 days, it will start to decay until we are able to take fees again
Any locked profit will be burned to offset the dilution incurred by any minted fee shares
Valuation
An Autopool tracks three valuations for any LP units it holds via a Destination Vault. These are the safe, spot, and mid point price of the LP tokens (see
https://docs.tokemak.xyz/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopilot-contracts-and-systems/pricing
). These values are used for different purposes in the life cycle of assets in the Autopool:
Higher of safe and spot: Used during deposit to value the assets held by the Autopool
Lower of safe and spot: Used during withdraw to value the assets held by the Autopool
Mid point: Used for general reporting and fee calculations
To value shares for general purposes the standard ERC4626
convertToAssets(uint256)
should be used.
Max Withdraw Value
Using different valuations depending on the operation means that to find the maximum amount of assets one would receive during a
redeem()
call we need something more than the standard
convertToAssets(uint256)
. For this, we have an extension to the standard function:
Copy
Max Deposit Value
Calculating the shares you'd receive on a deposit follows very closely to the previous example
Copy
Estimating Withdraw Value
Above we went through how the Autopool values the tokens it holds and how to calculate a max return value. However, there is another aspect to a
redeem()
call that can affect the assets returned to the user. An Autopool holds a certain percentage of assets in idle to cover small withdraws. However, if an attempted withdraw needs more assets than sit in idle, the Autopool will start the redemption process by going to the market first. This entails removing liquidity from one or more destinations, and swapping out of non-WETH assets. These swaps can result in slippage and fee's taken in the liquidity pool being swapped through. The Autopool will also ensure that any recent price positive movements in the LP tokens being liquidated are captured. All of this is considered slippage that is passed on to the user performing the
redeem()
.
To retrieve an accurate estimation of assets that would be returned one can use the
previewRedeem()
call. However, it should be noted that this call deviates from the ERC4626 spec in that it is a nonpayable function instead of a view function. No state changes are made as a result of the call, but to provide the estimate state changes are necessary which are later reverted. This should not be called on-chain.
Due to this possible slippage, it is important to note that any call to
redeem()
should be checked that an expected amount of assets were received and to revert if not.
Rebalancing
Assets can be rebalanced between destinations according the rules of the Autopools configured strategy. Autopools support the ERC3156 flash loan interface and can grant our Solver access to funds to be able convert them into a more desirable Destinations LP token.
Architecture
GIven that the creation of Autopools may vary widely depending on the type of Autopool being created (future looking), Autopools and their corresponding Factory are a 1:1 relationship. This differs from other factory+register+template relationships in our system:
Previous
Destination Vaults
Next
Autopool Contracts Glossary
Last updated
1 year ago
Was this helpful?