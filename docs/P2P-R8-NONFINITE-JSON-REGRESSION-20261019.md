# URP0 numeric decoding failure boundary

Research-only decoder hardening. Python JSON parsing accepts a very large exponent as a nonfinite float, while canonical JSON re-encoding rejects it. The URP0 decoder should consistently raise its public InviteError rather than a bare ValueError.

This branch wraps canonical re-encoding errors in InviteError. A regression test should construct a self-consistently checksummed offline descriptor with a numeric exponent in a validity field, then assert InviteError. The full repository unit suite and Windows candidate have not been run. No authentication, transport, gameplay, or release proof is claimed.
