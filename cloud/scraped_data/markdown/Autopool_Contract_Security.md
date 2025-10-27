# Autopool Contract Security

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/autopool-contract-security

---

With the exception of the SystemRegistry contract which uses an “onlyOwner” setup for security (which will be granted to a multisig and eventually a Governor contract), all other contracts follow a RBAC security system.
AccessController
src/security/AccessController.sol
This is largely an OZ AccessControlEnumerable contract with the setup functions exposed, however, instead of each contract managing their own permissions, they all reference this one through the
SecurityBase
contract.
Given the sensitive nature of this contract, it is one of the contracts that can never be changed or upgraded in the system.
SystemSecurity
src/security/SystemSecurity.sol
This contract allows us to coordinate operations across all Autopools in the system. This coordination falls into two areas:
Pausing
NAV operation coordination
Pausing
Via the usage of this contract, we are able to pause all Autopool operations in the system. Autopools can still be paused locally or one-by-one, but this gives us a way pause all of them in one go.
NAV Operation Coordination
Operations in an Autopool can be broken down into ones that can see nav/share go down, and ones that can’t. To ensure proper calculations, operations that
SHOULD NOT see
a nav/share decrease can never be executed within the context of those that can.
Operations that can see a decrease in nav/share:
Debt reporting -
updateDebtReporting()
Rebalances -
flashRebalance()
Operations that shouldn’t:
User balance management -
deposit() / mint() / redeem() / withdraw()
This restrictions applies cross-Autopool as well. An
updateDebtReporting()
call in one Autopool for example, blocks
deposit()
in all Autopools during its execution.
Pausable
src/security/Pausable.sol
A near duplicate of the OZ contract by the same name. However, this one incorporates our SystemSecurity contract to support our global-pause behavior. It is used only by our Autopools.
Previous
Autopool Contracts and Systems
Next
Stats
Was this helpful?