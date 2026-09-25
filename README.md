# PageLatch

Escrow that settles when a **live webpage** matches a **natural-language promise**.

Ordinary contracts cannot read the web. Oracles report numbers. PageLatch asks GenLayer validators to independently render a public URL, judge the promise, and then pay or refund.

Portal type: **Builder → Intelligent Contracts**

## Why this belongs on GenLayer

| Check | PageLatch |
| --- | --- |
| On-chain consequence | Escrow splits HONOR / DENY / PARTIAL |
| Judgment | Natural-language promise vs live page |
| Independently checkable evidence | Public URL validators can fetch |
| Neutral consensus | Payer wants DENY, recipient wants HONOR |
| Structured result | Discrete verdict + integer `payout_bps` |

Not a prediction market, quiz, dashboard, chatbot, or football-bet clone. The load-bearing decision is: *does this public page satisfy this promise?*

This matches GenLayer’s own “when to use” checklist: real payout consequence + judgment over public evidence + validators verify the outcome.

## Two modes

- **STATE** — does the live page currently satisfy the promise?
- **DELTA** — compared to the snapshot taken at `open_latch`, did the promised change happen?

DELTA is implemented in the contract (`_snapshot_page` at open). Studio proof below uses **STATE** with opposite claims on the same URL — the cleanest way to show the judgment is real.

## Equivalence

`gl.eq_principle.prompt_comparative` on a canonical JSON object (`sort_keys=True`):

- `verdict` must be identical across validators (`HONOR` | `DENY` | `PARTIAL`)
- `payout_bps` within 500 bps
- `evidence_quote` / `reason` may differ in wording

Funds move only after consensus, via internal balances + `withdraw` (pull pattern).

`deadline` is stored on the latch as client metadata (UX / future timeout policy). Settlement today is driven by `adjudicate`, not wall-clock expiry.

## Studionet proof (live)

Deployed and adjudicated on GenLayer Studio with **Normal (Full Consensus)**, 5 validators.

| Item | Value |
| --- | --- |
| Contract | `0x463C04B9d5e1173D0F060bE8E2BA0Ed10B1E408B` |
| Deployer | `0x7A3725154a2E6468F9549334394802e9E2822C2A` |
| Deploy tx | `0xad7aa8e3815574510a542dced1884ca4b0c6cafc511234da9f6ac26577851b72` |

### Test 1 — HONOR

| Field | Value |
| --- | --- |
| URL | `https://example.com/` |
| Promise | This domain is a documentation placeholder with an IANA reference |
| Mode | `STATE` |
| Latch id | `1` |
| Adjudicate tx | `0x1d7bc5f76bc4c9b3b7e890f4d42fbcf68ab4f1d7f508ef9912ec2a3b7cc88c64` |
| Status | FINALIZED · consensus Accepted |

```json
{
  "verdict": "HONOR",
  "payout_bps": 10000,
  "evidence_quote": "This domain is for use in documentation examples without needing permission.",
  "reason": "The page explicitly says the domain is for documentation examples, which matches a documentation placeholder. The text also indicates it is an example domain consistent with an IANA-referenced placeholder page."
}
```

### Test 2 — DENY

| Field | Value |
| --- | --- |
| URL | `https://example.com/` |
| Promise | This is the official White House website |
| Mode | `STATE` |
| Latch id | `2` |
| Open tx | `0x7e39e32f53241868bd3e4045740fc19ea629fd13779bd33f49547ac52017d06d` |
| Adjudicate tx | `0xb7192245b5a4e6ad0e7ccf207b7259895026bb1f22adef02c3abaef3d62350a8` |
| Status | FINALIZED · consensus Accepted |

```json
{
  "verdict": "DENY",
  "payout_bps": 0,
  "evidence_quote": "Example Domain",
  "reason": "The live page is a generic placeholder for documentation examples and contains no content or branding related to the White House."
}
```

**Same public page. Opposite natural-language claims. Opposite structured verdicts under full consensus.** That is the GenLayer thesis.

## Deploy yourself

1. Open [studio.genlayer.com](https://studio.genlayer.com)
2. Paste [`contracts/PageLatch.py`](contracts/PageLatch.py)
3. Create at least 5 validators
4. Deploy with **Normal (Full Consensus)**
5. Run the two example.com tests above

## Methods

| Method | Who | What |
| --- | --- | --- |
| `open_latch` | payer (payable) | Lock stake against URL + promise. DELTA takes a snapshot. |
| `claim_done` | recipient | Marks work complete (optional before adjudicate). |
| `adjudicate` | anyone | Render live page, structured verdict, credit balances. |
| `withdraw` | anyone with a balance | Pull pattern after settlement. |
| `get_latch` | view | Full record. |
| `get_balance` | view | Internal balance. |
| `get_next_id` | view | Next latch id. |

## Acceptance checklist (stewards)

- [x] Real Intelligent Contract (not frontend-only LLM)
- [x] Uses `gl.nondet.web.render` at execution time
- [x] Uses `gl.eq_principle.prompt_comparative` with discrete verdict field
- [x] On-chain consequence (escrow balances)
- [x] Live Studio proof: HONOR + DENY under Full Consensus
- [x] Public GitHub with single contract + README evidence
- [x] Not a football / quiz / prediction-market template clone

## Portal submission copy

**Type:** Builder → Intelligent Contracts  
*(Do not submit as Milestone until a Project is already accepted.)*

**Title:**

```
PageLatch — escrow that settles on a live webpage
```

**Description:**

```
PageLatch is an Intelligent Contract that locks escrow against a public URL and a natural-language promise. Settlement is not an admin key and not an oracle price. Validators independently render the live page, judge whether the promise holds, and release or refund.

Two modes:
• STATE — does the live page currently satisfy the promise?
• DELTA — compared to the snapshot taken at open, did the promised change actually happen?

Structured verdicts: HONOR (100% to recipient), DENY (100% refund), PARTIAL (split in bps). Equivalence is comparative: the verdict field must match across validators.

Studio proof (Studionet, Full Consensus, 5 validators):
- Contract: 0x463C04B9d5e1173D0F060bE8E2BA0Ed10B1E408B
- HONOR (example.com = documentation placeholder): 0x1d7bc5f76bc4c9b3b7e890f4d42fbcf68ab4f1d7f508ef9912ec2a3b7cc88c64
- DENY (example.com ≠ White House): 0xb7192245b5a4e6ad0e7ccf207b7259895026bb1f22adef02c3abaef3d62350a8

Not a prediction market, quiz, or football-bet clone. The load-bearing decision is: does this public page satisfy this promise?
```

**GitHub:** https://github.com/Sheikhzidan/PageLatch

## License

MIT — see [LICENSE](LICENSE)
