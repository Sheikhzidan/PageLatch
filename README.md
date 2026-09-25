# PageLatch

Escrow that settles when a **live webpage** matches a **natural-language promise**.

Ordinary contracts cannot read the web. Oracles report numbers. PageLatch asks GenLayer validators to independently render a public URL, judge the promise, and then pay or refund.

This is a GenLayer **Intelligent Contract** for Portal submission under **Builder → Intelligent Contracts**.

## Why this belongs on GenLayer

| Check | PageLatch |
| --- | --- |
| On-chain consequence | Escrow splits HONOR / DENY / PARTIAL |
| Judgment | Natural-language promise vs live page |
| Independently checkable evidence | Public URL validators can fetch |
| Neutral consensus | Payer wants DENY, recipient wants HONOR |
| Structured result | Discrete verdict + integer `payout_bps` |

Not a prediction market, quiz, dashboard, chatbot, or football-bet clone. The load-bearing decision is: *does this public page satisfy this promise?*

## Two modes

- **STATE** — does the live page currently satisfy the promise?
- **DELTA** — compared to the snapshot taken at `open_latch`, did the promised change happen?

DELTA is the unique wedge: escrow bonded to a verified webpage **diff**, which is the actual job an agent was hired to do.

## Equivalence

`prompt_comparative` on a canonical JSON object.

- `verdict` must be identical across validators (`HONOR` | `DENY` | `PARTIAL`)
- `payout_bps` within 500 bps
- quotes/reasons may differ in wording

Funds move only after consensus, via an internal balance + `withdraw` pull pattern.

## Deploy (Studionet)

1. Open [studio.genlayer.com](https://studio.genlayer.com)
2. Paste [`contracts/PageLatch.py`](contracts/PageLatch.py)
3. Create at least 5 validators
4. Deploy

## Steward test plan

Use the same contract, opposite promises:

1. `open_latch` → `https://example.com/`  
   Promise: *This domain is a documentation placeholder with an IANA reference*  
   → expect **HONOR**
2. `open_latch` → `https://example.com/`  
   Promise: *This is the official White House website*  
   → expect **DENY**
3. Optional DELTA: snapshot a GitHub README, edit it, `claim_done`, `adjudicate`

Attach both explorer txs as evidence.

## Methods

| Method | Who | What |
| --- | --- | --- |
| `open_latch` | payer (payable) | Lock stake against URL + promise. DELTA takes a snapshot. |
| `claim_done` | recipient | Marks work complete. |
| `adjudicate` | anyone | Fetch live page, structured verdict, credit balances. |
| `withdraw` | anyone with a balance | Pull pattern. Safer than pushing value during consensus. |
| `get_latch` | view | Full record. |

## Portal copy

**Type:** Builder → Intelligent Contracts (this week; do not use Milestone until a Project is accepted)

**Title:** PageLatch — escrow that settles on a live webpage

See the description in this README’s first sections. Keep the GitHub repo small: this file + one Python contract. Do not dump a vibecoded monorepo.

## License

MIT
