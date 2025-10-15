# Autopool Contracts and Systems

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems

---

The contracts were designed with a couple concepts in mind:
It is possible that Tokemak could run multiple, separate, instances of this system on the same chain and the majority of contracts would not be safe to share between the two.
Misconfigurations are a potential source of bugs and this is a highly configurable system. Any validations that can be performed during registration and setup, should.
To assist in enforcing these points, the system revolves around a SystemRegistry contract (
src/SystemRegistry.sol
), and most contracts inherit from a SystemComponent (
src/SystemComponent.sol
) contract that requires a reference to a SystemRegistry. These allow us to tie the various contracts together and provide a lookup point for the various contracts to talk to one another.
Previous
Autopool System High Level Overview
Next
Autopool Contract Security
Was this helpful?