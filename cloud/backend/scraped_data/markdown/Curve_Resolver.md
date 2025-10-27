# Curve Resolver

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/curve-resolver

---

Getting information generically about a given Curve pool can be a tricky task given the slight variations between their different types of pools. This is a task we need to perform in many different areas of the app and so this contract was built to assist in that.
Luckily, Curve provides a meta registry themselves that can perform this lookup. However, at the time of writing this, there is a type of pool that is not supported by their registry and that is their Stable-NG type pools. To get around this, the CurveResolver has a fallback method where it attempts to figure out the information based on the successful execution of various functions.
This approach currently works for the types of pools we are interested in supporting. Should new types of pools be introduced in the future, the approaches outlined may need to be re-evaluated.
Previous
Swap Router
Next
Message Proxy
Was this helpful?