# Pricing

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/pricing

---

The valuation of tokens is core to the operation of this system. All token valuations are performed through the
RootPriceOracle
and different approaches for pricing are used depending on the type of token (native or LP) and the intended usage of the price:
Types of Prices
“Safe” Prices
These are prices that are calculated/queried from off-chain sources. This includes sources such as Chainlink, Redstone, and Tellor. These are exposed through three calls on the
RootPriceOracle
:
getPriceInEth()
,
getPriceInQuote()
, and one of the return values of
getRangePriceLP()
These are mainly used for operations where we aren’t executing with the price at that moment. This can include pricing debt in the Autopools, calculating statistics, etc.
Spot Prices
These are prices that are calculated/queried from primarily on-chain sources. These are always in reference to a specific pool that want to know the spot price of the tokens from. To calculate these values, a small amount of token is trial swapped through a pool to determine its execution price and then any fees are factored back in.
For requests that don’t have the requested quote token as one of the tokens in the pools, “safe” prices are used to complete the steps in the conversion.
These prices are exposed through
getSpotPriceInEth()
and one of the return values of
getRangePriceLP()
.
Spot prices are checked against some tolerance when used within the system to ensure they are safe to use. The spot price of the token must be within some bps of the safe price. These are used during rebalance execution to measure impact on pools we are operating against as well as one of the ends of the
getRangePriceLP()
call.
Floor & Ceiling LP Prices
These prices are exclusively used in the Autopools when debt reporting has gone stale. While this should never actually be an occurrence, should a pool enter this state, debt that is stale will be re-valued using this method of pricing. This will take the worst price (depending on the operation that could be the highest or the lowest) between the safe and spot prices of all the tokens that constitute the LP token, and value all the reserves that back that LP back at that single price. This is to ensure that any potential manipulation that could be occurring cannot negatively impact the Autopool.
Architecture
The system-at-large will only ever interact with the RootPriceOracle. All specific implementations related to the method of pricing an asset are hidden behind here:
The majority of functions on the RootPriceOracle are not view functions even though they are performing “view” type operations. This is due to methods used for pricing. Since we use swaps to calculate prices, and we can’t count on every DEX to have a view operation to perform this, we have to keep the interface as payable.
Safe Price Call Flow
The following is an example call flow for resolving a complex price. We will assume that the requested price is for the $ABC token in ETH. $ABC token has an $ABC/USD feed through Redstone:
LP Price Call Flow
The following is an example call flow for resolving the safe and spot price of an LP token. We will assume this is a Curve pool:
Previous
Autopool Strategy
Next
Swap Router
Was this helpful?