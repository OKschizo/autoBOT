# Large Withdrawals

Source: https://docs.auto.finance/developer-docs/integrating/large-withdrawals

---

Autopools allow you to deposit and withdraw in the same asset, the base asset,and to do so on-demand. This means when your withdrawal is large enough to require pulling assets from the underlying LP markets you may incur slippage from swapping back into the Autopool's base asset.
By default, the Autopilot system is configured to be able to swap out of these assets all on-chain with no additional work or information needed. However the quality of trade-execution back into the base asset is limited by the liquidity present in the configured routes that are on-chain. We'll outline here how to provide your own routes to optimize withdrawal execution and to set limit slippage controls.
Determining Swap Amounts
The first step in providing your own routes is to make a rough estimate as to the tokens and amounts that the Autopool will attempt to swap out of. For a TL;DR version, we have provided a package that will give this information for an Autopool and share amount:
https://www.npmjs.com/package/@tokemak/autopilot-swap-route-calc
If you're able to use the package then you can skip the following section. However for those that wish to calculate these tokens manually, read on.
Calculating Manually
If you wish to calculate these values on your own, you should inspect the logic that is performed during the
redeem()
operation on the Autopool:
https://github.com/Tokemak/v2-core-pub/blob/main/src/vault/AutopoolETH.sol#L357
Some parts to highlight:
One cannot receive more than assets than the shares valued using withdrawal pricing
If there are enough assets in idle to cover the value of the shares, no swaps are needed
The destinations used to pull assets are picked from the withdrawal queue on the Autopool: `getWithdrawalQueue()`
Handling Swaps During Redemption
As with calculating the amounts to swap, we have an interface to get optimal swap executions as well. This is via an API that under the hood utilizes DEX aggregators such as 0x and Bebop. To call:
Copy
Where the
tokensToLiquidate
is the output from the package
@tokemak/autopilot-swap-route-calc
package above.
systemName
stays "gen3".
The
results
from the API output is what will be later passed into our Router for execution:
Copy
Custom Swap Handling
It's possible to use your own contracts as well during the swapping and redemption process instead our API and swapper contracts. To illustrate what would need to be done lets look at the execution flow.
During the
redeem()
process, our swapper contracts are engaged 0..n times based on the amount of shares being redeemed and the Destinations/markets we need to pull from to satisfy. For example:
User is redeeming 100 Autopool shares worth 102 ETH (idle only has 5 ETH so it can't cover)
The Autopool has 50 ETH worth of assets deployed to the first Destination in the withdrawal queue and 200 ETH worth of assets deployed to the second Destination in the withdrawal queue.
The first Destination is a wstETH/WETH and the second a pxETH/rETH
Lets assume all assets are priced at 1 ETH. 
We would expect our swapper contracts to be engaged 3 times:
Swap 25 wstETH into WETH
This swaps to WETH because the asset() on the Autopool is WETH
Since the second token in this Destination is already WETH, it is skipped for swapping
Swap 26 pxETH into WETH
Swap 26 rETH into WETH
We exhausted the 50 ETH worth of assets from the first Destination and then moved to the second to get the remainder
Using the output from our API as an example you'd construct an array of the
fromToken,toToken,target,data
for each of three tokens above, wstETH, pxETH, and rETH:
target
is the contract you want us to call
data
is the call data you'd want us to use to call your
target
Before your function is called the assets to be swapped will be transferred to the
target
Before the execution of the function ends, the contract should transfer the new assets back to the msg.sender.
Constructing the Final Transaction
Redemption with custom swap routes is only possible through our Autopilot Router multicall contract (see
Contract Addresses
).  There are multiple ways to construct the call but ultimately you are attempting give the Router access to your tokens (through approvals, sending, or having the Router pull them) and calling
redeemWithRoutes()
Previous
4626 Compliance
Next
Checking for Stale Data
Last updated
8 months ago
Was this helpful?