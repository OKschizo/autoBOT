# Tokemak Blog - Autopilot

URL: https://blog.tokemak.xyz/post/autopilot
Scraped: 2025-10-23T16:08:45Z

## Metadata

- **read_time**: 8 min read time

## Content

1. Introduction

‍

Liquidity provisioning remains fragmented. While manually providing liquidity, particularly to correlated trading pairs such as ETH LSTs/LRTs and stablecoins, individual liquidity providers (LPs) face a complex decision-making process involving a wide array of pools and DEXs, varying yields, and costs such as gas, slippage, and trading fees.

‍

In addition to the complexity of rebalancing liquidity, individual LPs are often priced out due to the associated costs, inevitably leading to underperformance. As a result, liquidity remains isolated and stagnant across pools, insensitive to changes in rates unless manual intervention occurs.

‍

Autopilot introduces automated liquidity (autoLP) to DeFi, which connects liquidity that was previously isolated across different pools through autonomous LP rebalances. This novel form of LP aggregation creates reactive liquidity which adapts dynamically to changes in rates. As such, LPs are able to passively outperform individual pools via a configurable set of options - Autopools - while retaining composability across DeFi.

‍

‍

2. Autopilot: LP Aggregation

‍

Autopilot enables a new way to LP through Autopools. These Autopools use the ERC-4626 standard and can be configured with various pools across different DEXs as destinations, thus creating customizable networks of automated liquidity. Once assets are deployed, Autopilot monitors the market, assesses fluctuations in yields taking into account a wide range of metrics, and autonomously rebalances liquidity for long-term LP outperformance.

‍

Using this approach, gas costs are dramatically reduced, and earnings are auto-compounded into the respective Autopool. Furthermore, users receive a composable receipt token that can be seamlessly integrated across DeFi.

‍

The user experience for Autopool LPs is simple: deposit ETH and receive autoXYZ. Autopilot will then autonomously rebalance liquidity across the underlying destinations. Using its on-chain verifiable decision-making process, Autopilot ensures transparent rebalance decisions and auditable strategies across a predefined set of assets and destinations. It is important to note that users can withdraw deposited funds at any time with no delays.

‍

For launch, Autopilot will be live on Ethereum mainnet and Base. The initial focus will be on ETH-denominated Autopools for LSTs and LRTs, with a particular emphasis on incentivizing the distribution of the respective receipt tokens, autoETH and autoLRT. Beyond ETH, the plan is to quickly expand to other asset classes, such as stablecoins. Built with modularity in mind, the architecture allows the integration of new assets and destinations in a seamless plug-and-play manner.

‍

Additionally, permissionless creation of Autopools will be introduced post-launch. This feature allows any user to create their own Autopool with a customized risk profile and corresponding receipt token. As a result, users have the flexibility to express individual risk preferences, meaning that the free market can determine new pool configurations for Autopools.

‍

Ultimately, Autopilot's goal as an LP Aggregator is to replace direct interactions with DEXs, acting as a funnel that routes all deposited liquidity based on market rates. This approach expands the addressable market for liquidity provision to any asset holder seeking passive earnings, while simultaneously enhancing market efficiency and overall liquidity. What DEX aggregators did for traders, Autopilot is doing for LPs.

‍

‍

3. Autopilot: System Overview

‍

The Autopilot system is designed with the goal of continuously allocating assets deposited into Autopools to destinations with the best risk-return profile. Rewards earned in the process are auto-compounded and redeposited into the respective Autopool. This section outlines a simplified overview of the system and an asset flow example.

‍

3.1. Strategy

‍

The Strategy contract is responsible for determining if a given liquidity rebalance is in the best interest of an Autopool. To achieve this purpose, Autopilot relies on the Stats System, which is responsible for providing all required signals (e.g., various types of yield) available on-chain. These signals are then stored and processed by “calculators” that are kept up to date through a keeper network.

‍

Among the strategy’s key features we have the following:

‍

Composite Return Metric - The Composite Return Metric is a score associated with destinations for liquidity within Autopools. This metric breaks down APRs into separate parts. As such, Autopilot has the flexibility of overweighting/underweighting different components for further optimization. A valid rebalance needs to verify an increase in this metric.

‍

Adaptive Rebalance Offset Period - The adaptive rebalance constraint is a gatekeeping condition for rebalances, which states that the expected return associated with a rebalance needs to be recouped over a given period. It is worth noting that this is a self-learning mechanism with a variable cost offset period that adapts to different market environments based on the observed yield volatility.

‍

Lastly, several other factors are accounted for in the strategy, such as total slippage (i.e., the total difference in the value of the in and out LP tokens) and lookback tests that verify an increase of the net asset value (NAV) over time.

‍

3.2. Solver

‍

The Solver is an off-chain component that proposes rebalance solutions to interchangeably convert assets and LP tokens, as well as LP token into other LP tokens. The rebalance solutions are proposed to the Strategy, once they satisfy the Strategy’s imposed constraints, a rebalance takes place.

‍

3.3. Autopilot: Flow of Assets

‍

‍

The following steps provide a simplified illustration of the flow of assets within Autopilot:

‍

Deposit - User deposits assets into Autopool. After this action, the Autopool has idle assets and the user gets the respective receipt token in return;

‍

Rebalance - After a certain threshold of assets is deposited into the Autopool, the Strategy backing it starts to accept proposals from the Solver. Once a proposal satisfies the constraints imposed by the Strategy, the proposed rebalance takes place, and assets are converted into LP tokens;

‍

Auto-compounding - On a periodic basis, rewards from destinations are claimed and collected via a keeper process. These tokens are then converted into the Autopool base asset;

‍

Debt Reporting - Each Autopool goes through a debt reporting during which the system re-values the LP tokens held by an Autopool. During that process, any available auto-compounded rewards are claimed and come into the Autopool as idle funds;

‍

Restart - With sufficient idle assets in the Autopool, another rebalance can occur. While this asset flow primarily focuses on idle-to-LP rebalances, it also applies to LP-to-LP rebalances, provided the proposed move results in a higher potential return and meets additional constraints imposed by the strategy.

‍

In other words, users deposit assets into Autopools, the stats contracts provide on-chain market information, and the solver proposes rebalances to be validated by the strategy. For a proposed rebalance to be accepted, it must meet the strategy's constraints.

‍

4. Liquid Auto Tokens (LATs) and Permissionless Autopools

‍

Liquid Auto Tokens (LATs) represent yield-bearing Autopool receipt tokens (e.g., autoETH). In essence, LATs are tokenized automated liquidity networks backed by LP positions. Once the permissionless creation of Autopools is live, anyone will be able to launch Autopools with customizable risk profiles and issue the respective LATs. As such, Autopilot becomes a platform where DAOs, risk managers, and individual users can launch Autopools. This permissionless feature allows users to express individual risk preferences, thus letting the free market determine new pool configurations for Autopools.

‍

‍

4.1. DAOs

‍

For web3 projects, LATs provide a new way to combine utility with distribution. DEXs, asset issuers, and L2s, can customize Autopools with the preferred pool selection. Using the respective LAT, it becomes possible to eliminate the overhead associated with the complexity and monitoring required from LPs, streamlining liquidity provision through a single token. 

‍

As an example, a DEX can select a set of pools (e.g., correlated ETH pairs), create the respective Autopool, and issue its own project branded LAT (e.g., xyzETH). Once set up, the user experience is simple: provide ETH, receive xyzETH, and all the underlying liquidity remains optimally deployed according to market rates, while remaining within the underlying DEX ecosystem. As a result, this DEX ecosystem is now tokenized and can be exported through its own LAT which remains composable across DeFi.

‍

Examples of possible DeFi integrations include utilizing LATs as collateral, integrating LATs into yield marketplaces to trade liquidity rates, and leverage LATs. Through the tokenization of automated liquidity networks, providing liquidity to a set of pools becomes as simple as swapping tokens or making deposits. This approach creates passive yield opportunities for users, which retain all underlying liquidity within a single ecosystem, thus promoting sticky liquidity and broadening the addressable market.

‍

‍

4.2. Risk Managers

‍

As DeFi evolves, new protocols are moving away from vertically integrated approaches, where a single protocol manages all aspects of a system, toward open and modular models. These models allow different participants to contribute specialized skills.

‍

New money markets such as Morpho Blue, or modular restaking platforms like Mellow, rely on architectures that allow for the customization of risk profiles by external actors. This allows risk managers to curate new product offerings with different risk-adjusted profiles.

‍

Autopilot is evolving in this direction with the integration of permissionless Autopools in its roadmap. This allows Tokemak to position itself as a platform where specialized risk managers can create customized Autopools with different configurations of pools and parameters, and issue the respective LATs. Through this open approach, Autopilot aims to expand its distribution and cater to specific market segments, such as institutional LPs.

‍

4.3. Individuals

‍

Autopilot's modular approach allows individual users to create custom Autopool configurations when existing options don't meet their risk profiles. Therefore, individuals can define pool compositions and parameters, thus issuing LATs that meet specific user needs.

‍

5. Conclusion

‍

Autopilot creates automated liquidity networks which are customizable and composable. As an LP Aggregator, Autopilot connects liquidity across pools and DEXs thus enabling a new way to LP. It achieves this by monitoring the market using various on-chain signals. These signals are then used to autonomously rebalance assets deposited into Autopools (ERC-4626). As such, Autopools represent automated liquidity networks tokenized through LATs, which can be utilized across DeFi. 

‍

Furthermore, Autopilot allows LPs to long-term outperform any constituent pools included in an Autopool. This is achieved while maintaining composability across DeFi through LATs and significantly reducing gas costs for users compared to the current LP experience. By integrating different AMM models in a plug-and-play manner, Autopilot abstracts away one of the core challenges of manual liquidity provision: differentiating between AMM models.

‍

Post-launch, Autopilot will introduce permissionless Autopools. As such, users can create new Autopools and customize risk profiles through the selection of pools and parameters. This open model allows DAOs, risk managers, and individuals to create and curate new risk profiles tailored to different market segments, ranging from retail to institutional LPs. Instead of pursuing a closed vertical approach, Tokemak becomes an open platform enabling external participants to launch Autopools and issue LATs.

‍

In summary, manual liquidity provision is a market inefficiency solved by Autopilot. Using Autopools, LPs can access automated liquidity networks tokenized through LATs, which remain composable across DeFi. As a platform where anyone can create Autopools, Autopilot allows DAOs, risk managers, and individuals to build customized risk profiles for different LP market segments. For DeFi, the evolution from Tokemak v1 to v2 marks the transition from manual to automated LPing. On Autopilot, liquidity becomes reactive.

‍

Autopilot is currently undergoing a final full system audit - the Guarded Launch, with Tokemak treasury deployed assets, is currently live. Users can already begin earning autoETH by locking TOKE now. When the full system audit concludes, Autopilot will be open to public deposits in the first Autopool.

‍

Join Tokemak Autopilot's Guarded Launch here.

‍