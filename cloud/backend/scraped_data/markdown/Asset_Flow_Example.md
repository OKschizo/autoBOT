# Asset Flow Example

Source: https://docs.auto.finance/auto-pools-protocol/protocol-mechanics/asset-flow-example

---

To understand the general architecture and functioning of the system, it helps to consider a simplified flow of assets within the system:
Deposit
– User deposits assets into an autopool. After this action, the autopool has idle assets and the user gets the respective receipt token in return;
Rebalance
– After a certain threshold of assets are deposited into the autopool, the Strategy backing it starts to accept proposals from the Solver. Once a proposal satisfies the constraints imposed by the Strategy, the assets in the autopool are sent to the Solver which will then return LP tokens to the autopool;
Auto-compounding
– On a periodic basis, rewards from destinations are claimed and collected via a keeper process. These tokens are then converted into the autopool base asset;
Debt Reporting
– Each autopool goes through a debt reporting where the system re-values the LP tokens held by that autopool. During that process, any available auto-compounded rewards are claimed and come into the autopool as idle funds;
Restart
– With sufficient idle assets in the autopool, another rebalance can occur.
In other words, users deposit assets into autopools, the stats contracts provide on-chain information about the market, and the solver proposes rebalances to the strategy. To be accepted, the proposed rebalance must meet the strategy's constraints.

The above outline focused on idle → LP rebalances but the rebalance step can occur for LP → LP rebalances as well. So long as the proposal results in a higher potential return (and satisfies other constraints) it can be executed.
Previous
Components & Logic
Next
Autopool Receipt Tokens
Last updated
1 month ago
Was this helpful?