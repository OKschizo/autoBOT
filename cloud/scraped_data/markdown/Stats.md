# Stats

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/stats

---

The Stats System is responsible for making all required signals (e.g., staking yield, fee yield, incentive yield, etc) available on-chain. These signals are read by the Strategy to determine if a rebalance is in the best interest of its Autopool. A
Calculator
is responsible for storing, augmenting, and cleaning data required to provide one of those signals. Let’s take an example Destination and see how it’s stats are built:
Curve osETH/rETH + Convex Staking
Stat calculators depend on each other to build the full picture of a Destination, with only the top-most calculator being referenced directly by the DestinationVault. In this case, the top-most calculator is the
ConvexCalculator
. This calculator is an example of an Incentive calculator. LP tokens staked into Convex automatically earn CRV and CVX. This pool is also configured with SWISE and RPL tokens as extra rewards. And so, some annualized amount of CRV, CVX, SWISE, and RPL will be reported to the Strategy where it will calculate what the yield of those tokens are.
As a dependency, the
ConvexCalculator
takes a reference to a calculator responsible for providing stats about the DEX pool itself, a
CurveV1PoolNoRebasingStatsCalculator
(V1 calculators work for both Stableswap and Cryptoswap pools). This calculator provides the trading fee yield for the pool.
The last piece(s) are the stats about the LST tokens themselves, osETH and rETH. These calculators,
OsethLSTCalculator
and
RethLSTCalculator
, were provided to the
CurveV1PoolNoRebasingStatsCalculator
as dependencies when it was created. These calculators provide stats such as the base yield and price-to-book value.
With all of these calculators each providing their own data to the overall picture, a Strategy can get an accurate reading of a Destinations return.
Types of Calculators
Incentive - Responsible for tracking the return of the incentives available when staking in Convex/Aura/Maverick/etc.
DEX - Responsible for tracking the trading fee yield of a given DEX pool
LST - Responsible for tracking the base yield and backing of an LST
Keeping Data Up-to-Date
A keeper network is used to periodically snapshot new data. Each calculator type defines the frequency and conditions under which a snapshot should be taken. Importantly, each calculator only stores the required information to provide its stats. If it needs to provide stats from another calculator, those are read at the time of the request to ensure that data is consistent.
Architecture
Previous
Autopool Contract Security
Next
Autopool Strategy
Was this helpful?