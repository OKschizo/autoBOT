# Checking for Stale Data

Source: https://docs.auto.finance/developer-docs/integrating/checking-for-stale-data

---

It is our recommendation to check for stale debt reporting before performing a read or write operation against the Autopool. While our systems strive to ensure that the reporting information is always up to date, outages or other network issues have the possibility to prevent this. Should the debt reporting data be stale, users shares and or value can be misrepresented.
To check for this state the Autopool exposes a
oldestDebtReporting()
function. If this returned timestamp is older than 1 day, you should prevent your operation from executing.
Previous
Large Withdrawals
Next
Community Resources
Last updated
6 months ago
Was this helpful?