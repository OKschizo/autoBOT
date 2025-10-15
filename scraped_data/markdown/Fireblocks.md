# Fireblocks

Source: https://docs.auto.finance/using-the-app/with-wallet-services/fireblocks

---

Fireblocks is a highly configurable wallet-as-a-service that provides users many protections while transacting on a blockchain. Depending on the settings of your wallet, you may need additional configuration or transaction policy updates to be able to fully utilize the Autopilot UI.
Listing Assets
To ensure you can see the balance of the Autopool tokens after depositing you can you list them in your workspace. This can be done from the "Assets" section in your console:
In the search box you can search for "Tokemak" to see any existing assets. If the Autopool token does not appear in the results, click the "List asset" link at the bottom of the search results:
Select the appropriate blockchain in the modal that appears, Ethereum, Base, Sonic, etc., and continue. You will then be prompted to enter the contract address for the Autopool you wish to list. All of our Autopool contract addresses can be found on this page:
Contract Addresses
. Common addresses are:
Ethereum Mainnet
autoETH:
0x0A2b94F6871c1D7A32Fe58E1ab5e6deA2f114E56
autoLRT:
0xE800e3760FC20aA98c5df6A9816147f190455AF3
balETH:
0x6dC3ce9C57b20131347FDc9089D740DAf6eB34c5
baseETH:
0xAADf01DD90aE0A6Bb9Eb908294658037096E0404
dineroETH:
0x35911af1B570E26f668905595dEd133D01CD3E5a
autoUSD:
0xa7569A44f348d3D70d8ad5889e50F78E33d80D35
Base Mainnet
baseETH:
0xAADf01DD90aE0A6Bb9Eb908294658037096E0404
Confirm the details on the final page of the modal and click "List asset":
Note: The asset may not show immediately in the search results after listing but should after a short period of time.
Repeat the process for any additional tokens you wish to list.
Enabling Contract Interactions
In addition to the Autopool you are wanting to interact with, the Autopilot UI relies on a router contract to streamline transactions. Depending on your wallet settings, both of these contracts may need configuration within your wallet.
Through a combination of whitelisting and your transaction policy, you'll need to enable transfers, approvals, contract calls, and optionally signing messages to the Autopool. The exact settings that are required depend on your existing setup.
The latest addresses can always be found on our
Contract Addresses
page but at the time of writing the routers are:
Ethereum Mainnet -
0x37dD409f5e98aB4f151F4259Ea0CC13e97e8aE21
Base Mainnet -
0xa18B89225491230fDb1883cFbda65E7931606931
Default Transaction Policy
The default transaction policy for Fireblocks allows contract calls and approvals to any contract but transfers only to whitelisted addresses. Follow the instructions in the following
Whitelisting
section for details on adding the router and Autopool.
Custom Transaction Policy
If you utilize a custom transaction policy then you'll need to ensure you have the proper rules in place to cover the calls the Autopilot UI will make. Given that these settings are highly dependent on your wallets configuration we won't go over the exact entries but in some form the policy should allow:
To the Autopilot Router
Transfers
Contract Calls (both approval and deployment)
Approvals
To the Autopool (autoETH, autoUSD, etc)
Transfers
Contract Calls (both approve and deployment)
Approvals
For reference, these "allow" rules are sufficient to cover deposit/withdraw/stake/unstake in our UI:
Note: "2 venues" here are the Autopilot Router and the Autopool (autoUSD, autoETH, etc)
Approvals
When withdrawing assets or staking them, the Autopilot UI defaults to gas-less approvals. If you wish to use them, you will need to setup a rule in your transaction policy to allowed Typed Messages. We would recommend disabling gas-less approvals in the UI and using standard approvals. To disable, in the Autopilot UI find the gear icon at the top right of the Withdraw/Stake tab. and toggle the "Disable gas-less approval" option:
Whitelisting
If you do not allow transactions with non-whitelisted destinations then you must add both contracts to the "Whitelisted addresses" section in your wallet. To check this setting you can go to the gear icon in the top right of your console -> General Tab -> One-time address transactions. If this setting is not enabled (the button will say "Allow" if this is the case), then proceed with adding the addresses.
To add the addresses, in your console go to the "Whitelisted addresses" page from the left-hand menu. In the top-right of the page section, click the "Create wallet" button. This should give you the "Create whitelisted wallet" model:
Since these are both contracts you'll be interacting with, select the "Contract" type. Let's handle the router first. Give it a name that you'll recognize such as "Tokemak Autopilot Router" and click Create Wallet. This should create and take you to the next step where you can add the actual router address:
Click "Add address" on this page and select the appropriate blockchain from the list. You should now be prompted to add the address:
Once you have entered the address and clicked
you are finished with this contract. Repeat the steps with the Autopool address which you can find above.
Previous
With Wallet Services
Next
Troubleshooting
Last updated
5 months ago
Was this helpful?