# Tokemak Blog - Autopilot - Guarded Launch Announcement

URL: https://blog.tokemak.xyz/post/autopilot-guarded-launch-announcement
Scraped: 2025-10-15T21:14:02Z

## Metadata

- **read_time**: 4 min read

## Content

Intro

The birth of Autopilot has arrived, beginning with a “guarded launch” to ensure the security and integrity of the system. During this phase, only Tokemak treasury assets will be deployed through Autopilot. Once the system has been sufficiently validated, it will open for external deposits. Please read below for more information regarding what to expect from the guarded launch, as well as how to participate:

Tokemak v2 – Autopilot

Autopilot represents a new way to LP, automatically optimizing deployments of your ETH by rebalancing across a known set of trusted DEXs and stable-pools, auto-compounding your rewards and saving gas costs.

Autopilot is designed with the goal of continuously allocating an LP portfolio for long-term outperformance. This is achieved with the following key features:



Composite Return Metric: Autopilot input;
Rebalance Constraint: Gatekeeper for Rebalances;
Adaptive Rebalance Constraint: Self-learning control;
Solver: Off-chain component responsible for Rebalances;


The Composite Return Metric is a score associated with each destination integrated on Autopilot. This metric breaks down APRs into separate parts. As such, Autopilot has the flexibility of overweighting/underweighting different components for further optimization.

Additionally, the rebalance constraint is a gatekeeping condition for rebalances, which states that the expected return over the cost offset period needs to exceed the rebalance cost. It is worth noting that this is a self-learning mechanism with a variable cost offset period that adapts to different market environments.

Lastly, rebalances are handled by the Solver. This intent-based architecture has an off-chain component where solvers can propose rebalance solutions to the Autopilot contract, while an on-chain component checks if the proposed solution constitutes an improvement and does not violate imposed constraints.

The Guarded Phase

The guarded phase precedes Autopilot’s open public launch. Although ETH yield optimization is a primary objective of Autopilot, the guarded phase focuses on testing and safety above yield optimization. Its objective is to validate the integrity of the system and rebalancing logic as outlined here.

The guarded phase supports the core Autopilot functionality intended to be supported at the open launch. At the same time it restricts aspects of the system to enable Tokemak to test under specific conditions.

During the guarded phase Tokemak will be the only depositor into the Guarded Autopool. Based on the reaching successful checkpoints, the initial ETH deposit will be scaled up.

Assets, DEXs and DEX pools will also initially be limited, and will be expanded over the course of the guarded phase. Reference here for current checkpoints and expansions. By the end of the guarded phase the system is intended to reflect the full set of features, assets, DEXs and pools by Autopools at open launch.

Autopilot will undergo two additional audits in parallel with the guarded phase. Audits will include an additional full-system audit, in order to maintain Tokemak's rigorous security standards.

Participating in the Guarded Phase (locking TOKE)

Tokemak v2 will introduce redesigned tokenomics tailored to its functionality. Meanwhile, TOKE holders, current Liquidity Directors and accTOKE holders can engage in the guarded launch by either migrating and/or locking their TOKE tokens.

Locked TOKE will commence earning rewards on Wednesday, March 6, 2024. autoETH rewards are calculated based on the system earnings of the previous week and are distributed retroactively. Therefore, the first rewards will begin accruing on Wednesday, March 13, 2024. In contrast to accTOKE, for which rewards were distributed in one lump sum, the autoETH rewards drip out linearly over the duration of the week. Since rewards are earned in the preceding week, this also implies that users who withdraw TOKE will continue to receive rewards due to them.

Please note that users will be able to withdraw their rewards after the guarded phase has been completed and the system is opened up.

Find below a breakdown of the steps for the different types of holders:


accTOKE holders:

Current accTOKE holders, referring to TOKE that was locked into accTOKE before the rollover on Wednesday, February 28, 2024, do not need to migrate. They will seamlessly start earning autoETH rewards on Wednesday, March 6, 2024. If you do not wish to partake, please withdraw your TOKE.

Liquidity Directors:

Currently staked TOKE has to be migrated in order to partake. The mechanics follow the logic of the existing system, meaning a user has to be locked for a full cycle before earning rewards. LD reward emissions will end on March 6th, meaning that LDs that wish to partake in the guarded phase need to migrate by March 5th, in order to be included in the following week of rewards. Please note that LDs were always subject to missing a cycle of rewards when moving over to accTOKE. If you do not wish to partake, please withdraw your TOKE.


To migrate your TOKE, use the “MIGRATE DEPOSITED TOKE” option in the accTOKE module:

Liquid TOKE holders:

To earn autoETH rewards, lock your TOKE. Remember, after your TOKE is locked into accTOKE, rewards are earned retroactively (for the prior week), and your TOKE must remain locked for a full cycle.

‍