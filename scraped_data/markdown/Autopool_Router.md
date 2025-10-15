# Autopool Router

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/autopool-router

---

The Autopool Router is the main entry for users in the system. This is a multicall-type contract where the exposed functions are designed to be chained together to perform various operations. This can include but is not limited to:
Depositing into an Autopool and staking the tokens into a rewarder:
deposit(autoPool, router, amount, min)
approve(autoPool, rewarder, max)
stakeVaultToken(autoPool, max)
Migrating from one Autopool to another
withdrawVaultToken(autoPool, rewarder, amount, true)
selfPermit(autoPool, amount,….)
redeem(autoPool, router, amount, min)
approve(weth, autoPool2, max)
depositBalance(autoPool2, router, min)
stakeVaultToken(autoPool2, max)
The router also has the ability to swap tokens utilizing one of the AsyncSwappers configured in our system. Whether or not a swap can be utilized depends on the type of operation being performed. If we are able to know the exact number of input tokens upfront then it can be performed. Otherwise, we cannot.
Router should hold no balance
Given the flexibility of the Router it is possible to leave funds in the contract should the order of operations be incorrect. Those funds can then be withdrawn by anyone. This is expected. The Router will be integrated into our front-end and only specific flows will be supported ensuring that all token balances are sent back to the user when appropriate.
Previous
accTOKE
Next
Liquidation
Last updated
1 month ago
Was this helpful?