# Message Proxy

Source: https://docs.auto.finance/developer-docs/contracts-overview/autopool-eth-contracts-overview/autopool-contracts-and-systems/message-proxy

---

This contract is an interface to be able push data or events to other chains. It is exposed to the rest of the system as a generic interface but currently relies entirely on Chainlinks CCIP. It is designed to support a couple core features:
Fan-out messaging. Given a sender and message type, send the provided data to one or many destination chains
Retries. The last message of a given sender+type can be re-sent to a destination. This serves a few purposes
Should CCIP ever be down and messages unable to be sent, we should be able to get the data off that we need when it comes back online
Our contract could be out of funds when the send is attempted. We need processes that send the message to continue without reverting, but we want to be able to send that message eventually
Seeding information when standing up the destination chain. Some messages have large delays between them being sent. This can make standing up dependent contracts on the destination difficult and time consuming. Being able to re-send the last message ensures we have the information we need as soon as we can.
Usage
Current usage is restricted to just the LST calculators through the LSTCalculatorBase. The stats related to LSTs are specific to their native chain.
Previous
Curve Resolver
Next
accTOKE
Was this helpful?