# Swap Router

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/swap-router

---

When there is a withdraw from an Autopool, a couple things can happen. If there are enough assets to cover the withdrawal sitting idle in the Autopool, then all of the assets come from there. However, if there is not, then we must pull from the market. Just retrieving the LP positions doesn’t help the user, we must provide them back their funds in the base asset of the Autopool. This is where the SwapRouter comes in.
The SwapRouter contains routes for all the tokens that make up the constituents of any LP token we support, back to the base asset of the Autopool. This is a list that will be kept up to date by the team to ensure users receive the best execution when exiting the pools.
Example Routes
The routes can be simple or complex. We can use the same pools we are in as Destinations or completely different pools should there be better execution.
Simple Example for TokenA → TokenD:
Swap TokenA → TokenD in Balancer TokenA/TokenD Pool
Complex Example for TokenA → TokenD
Swap TokenA → TokenB in Curve TokenA/TokenB Pool
Swap TokenB → TokenC in Uni V3 TokenB/TokenC Pool
Swap TokenC → TokenD in Balancer TokenC/TokenD Pool
Swap Adapters
The chaining of operations all happen at the SwapRouter level. The only thing an adapter needs to be able to do is to swap between two tokens and validate that a given configuration is supported in the specified pool. They are only callable by the Currently we support:
Balancer Pools
Curve StableSwap Pools
Curve CryptoSwap Pools
UniV3 Pools
Previous
Pricing
Next
Curve Resolver
Was this helpful?