# PageLatch

Escrow that settles when a **live webpage** matches a **natural-language promise**.

Validators independently render a public URL, judge the promise in natural language, and release or refund stake. No admin key. No price oracle.

Contract: [`contracts/PageLatch.py`](contracts/PageLatch.py)

## Why GenLayer

| Requirement | How PageLatch uses it |
| --- | --- |
| On-chain consequence | Escrow → HONOR / DENY / PARTIAL payout |
| Judgment | Natural-language promise vs live page text |
| Public evidence | Any `http(s)` URL validators can fetch |
| Adversarial setup | Payer wants DENY, recipient wants HONOR |
| Consensus-safe output | Discrete `verdict` + integer `payout_bps` |

Uses `gl.nondet.web.render` and `gl.eq_principle.prompt_comparative` at execution time. Not a prediction market, quiz, dashboard, or football-bet template.

## Modes

- **STATE** — does the live page currently satisfy the promise?
- **DELTA** — compared to the snapshot taken at `open_latch`, did the promised change happen?

## Equivalence

Leaders and validators return canonical JSON (`sort_keys=True`):

```json
{
  "verdict": "HONOR | DENY | PARTIAL",
  "payout_bps": 0,
  "evidence_quote": "...",
  "reason": "..."
}
```

Comparative principle: `verdict` must match exactly; `payout_bps` within 500 bps; quotes/reasons may differ in wording.

Balances are credited after consensus. Parties pull funds with `withdraw`.

## Studio proof

Studionet · **Normal (Full Consensus)** · 5 validators

| Item | Value |
| --- | --- |
| Contract | `0x463C04B9d5e1173D0F060bE8E2BA0Ed10B1E408B` |
| Deployer | `0x7A3725154a2E6468F9549334394802e9E2822C2A` |
| Deploy | `0xad7aa8e3815574510a542dced1884ca4b0c6cafc511234da9f6ac26577851b72` |

### HONOR — latch `1`

- URL: `https://example.com/`
- Promise: *This domain is a documentation placeholder with an IANA reference*
- Mode: `STATE`
- Tx: `0x1d7bc5f76bc4c9b3b7e890f4d42fbcf68ab4f1d7f508ef9912ec2a3b7cc88c64` (FINALIZED)

```json
{
  "verdict": "HONOR",
  "payout_bps": 10000,
  "evidence_quote": "This domain is for use in documentation examples without needing permission.",
  "reason": "The page explicitly says the domain is for documentation examples, which matches a documentation placeholder."
}
```

### DENY — latch `2`

- URL: `https://example.com/`
- Promise: *This is the official White House website*
- Mode: `STATE`
- Open: `0x7e39e32f53241868bd3e4045740fc19ea629fd13779bd33f49547ac52017d06d`
- Adjudicate: `0xb7192245b5a4e6ad0e7ccf207b7259895026bb1f22adef02c3abaef3d62350a8` (FINALIZED)

```json
{
  "verdict": "DENY",
  "payout_bps": 0,
  "evidence_quote": "Example Domain",
  "reason": "The live page is a generic placeholder for documentation examples and contains no content or branding related to the White House."
}
```

Same page, opposite claims, opposite verdicts under full consensus.

## Interface

| Method | Type | Description |
| --- | --- | --- |
| `open_latch(recipient, url, promise, mode, deadline)` | write · payable | Lock stake; DELTA snapshots the page |
| `claim_done(latch_id)` | write | Recipient marks work complete |
| `adjudicate(latch_id)` | write | Render page, settle balances |
| `withdraw()` | write | Pull credited balance |
| `get_latch(latch_id)` | view | Full latch record |
| `get_balance(who)` | view | Internal balance |
| `get_next_id()` | view | Next latch id |

## License

MIT
