# accTOKE

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/acctoke

---

accToke gives users the ability to stake their TOKE and earn rewards in WETH. This contract is largely based on
https://docs.oeth.com/governance/ogv-staking
.
Differences to call out
Rewards can accrue in the contract for a user and don’t actual claiming
Rewards are queued instead of being on an emissions schedule. Rewards will not be added in large amounts to ensure there can’t being meaningful gaming of, and spikes in,
accRewardPerShaer
Interactions
Generally accToke sits on the outside of the platform. It doesn’t have a integration into the Autopilot router. The exception to this is within the AutopoolMainRewarder. We optionally have the ability to configure that if TOKE is the token being rewarded, it can be staked for a period of time into AccToke upon claim.
Previous
Message Proxy
Next
Autopool Router
Was this helpful?