# 4626 Compliance

Source: https://docs.auto.finance/developer-docs/integrating/4626-compliance

---

Autopools are implemented on top of the ERC-4626 vault standard but do no strictly adhere to the spec. The changes and important information for integration are listed below.
View Functions as Non-Payable
Due to how pricing and estimation is handled within the Autopool the following functions which are to be
view
functions per the spec are instead implemented as non-payable. Its important to note that these functions DO NOT actually make any state updates but utilize a "read-through-revert" pattern to simulate certain values:
previewDeposit()
previewMint()
previewRedeem()
previewWithdraw()
maxDeposit()
maxMint()
maxRedeem()
maxWithdraw()
Slippage
Depending on the conditions of the Autopool, the overall market, and the timing of the debt reporting process slippage may be encountered on both entering and exiting the Autopool. It is very important to always check the shares received on entering, and the assets received on exiting, are greater than an expected amount.
Future functionality of Mint + Withdraw
The use of the
mint()
and
withdraw()
flows is not advisable. While currently functional, they may begin to revert in the future. These functions also consistently have more slippage, and use more gas, than their
deposit()
and
redeem()
counterparts due to the necessary calculations performed.
Exiting the Autopool based on size
The Autopools make an effort to support depositors of any size. Given the number of destinations (DEX's, lending markets, etc) that assets may be deployed to, this quickly becomes a trade-off game involving the assets being worked with, slippage conditions in the market, and the gas needed to retrieve them.
The most gas-efficient route is to pull all the assets from either idle or from as few destinations as possible. This is the default behavior through
redeem()
. The Autopilot system keeps a cached set of swap routes on-chain to get out of the assets deployed to these destinations but, depending on size, these routes may be exhausted. To combat this, dynamic swap routes are able to be supplied by the caller. See
Large Withdrawals
for more information.
On the other end of the spectrum, when the size is so large that slippage outweighs the gas impact, additional functions are being added outside of the 4626 spec. These functions will return the pro-rata share of the underlying assets (LSTs, LRTs, USD derivatives, etc) owned by the user giving them complete control of how/when/if they return to the deposited asset.
It is up to the caller to decide the method for performing the exit.
Previous
Integrating
Next
Large Withdrawals
Last updated
6 months ago
Was this helpful?