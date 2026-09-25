# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
PageLatch — escrow that settles when a live webpage matches a promise.

Ordinary contracts cannot read the web. Oracles report numbers. PageLatch asks
GenLayer validators to independently render a public URL, judge a natural-language
promise against that live page, and then pay or refund.

Two modes:
  STATE  — does the live page currently satisfy the promise?
  DELTA  — compared to the snapshot taken at open, did the promised change happen?

Verdicts are discrete so consensus can close:
  HONOR   → 100% of the stake to the recipient
  DENY    → 100% refund to the payer
  PARTIAL → split by payout_bps (0–10000)

This file is Studio-ready. Deploy as-is on https://studio.genlayer.com
"""

from genlayer import *
from dataclasses import dataclass
import json
import typing


@allow_storage
@dataclass
class LatchRecord:
    payer: Address
    recipient: Address
    url: str
    promise: str
    mode: str
    snapshot: str
    amount: u256
    deadline: u256
    status: str
    payout_bps: u256
    evidence_quote: str
    reason: str


def _norm_text(raw: str, limit: int) -> str:
    collapsed = " ".join((raw or "").split())
    return collapsed[:limit]


def _parse_verdict(payload: typing.Any) -> dict:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}
    if not isinstance(payload, dict):
        payload = {}

    verdict = str(payload.get("verdict", "DENY")).upper().strip()
    if verdict not in ("HONOR", "DENY", "PARTIAL"):
        verdict = "DENY"

    try:
        payout_bps = int(payload.get("payout_bps", 0))
    except Exception:
        payout_bps = 0

    if verdict == "HONOR":
        payout_bps = 10000
    elif verdict == "DENY":
        payout_bps = 0
    else:
        payout_bps = max(0, min(10000, payout_bps))

    return {
        "verdict": verdict,
        "payout_bps": payout_bps,
        "evidence_quote": str(payload.get("evidence_quote", ""))[:280],
        "reason": str(payload.get("reason", ""))[:400],
    }


class PageLatch(gl.Contract):
    owner: Address
    next_id: u256
    latches: TreeMap[str, LatchRecord]
    balances: TreeMap[Address, u256]

    def __init__(self):
        self.owner = gl.message.sender_address
        self.next_id = u256(1)

    def _credit(self, who: Address, amount: u256):
        if amount == u256(0):
            return
        current = self.balances.get(who, u256(0))
        self.balances[who] = current + amount

    def _snapshot_page(self, url: str) -> str:
        def capture() -> str:
            page = gl.nondet.web.render(url, mode="text")
            excerpt = _norm_text(page, 6000)
            prompt = (
                "You are snapshotting a public webpage for a later before/after check.\n"
                "Write 6-8 factual bullets of what the page currently shows.\n"
                "No opinions. No extra keys.\n"
                "Return JSON: {\"snapshot\": \"bullet1 | bullet2 | ...\"}\n\n"
                f"PAGE:\n{excerpt}"
            )
            result = gl.nondet.exec_prompt(prompt, response_format="json")
            if isinstance(result, dict):
                return _norm_text(str(result.get("snapshot", "")), 1500)
            return _norm_text(str(result), 1500)

        return gl.eq_principle.prompt_comparative(
            capture,
            principle="The snapshot must describe the same page facts. Wording may differ.",
        )

    @gl.public.write.payable
    def open_latch(
        self,
        recipient: str,
        url: str,
        promise: str,
        mode: str,
        deadline: u256,
    ):
        stake = gl.message.value
        if stake == u256(0):
            raise Exception("attach a non-zero stake")
        if not url.startswith("http://") and not url.startswith("https://"):
            raise Exception("url must be http(s)")
        if len(promise.strip()) < 12:
            raise Exception("promise is too short")

        mode_norm = mode.upper().strip()
        if mode_norm not in ("STATE", "DELTA"):
            raise Exception("mode must be STATE or DELTA")

        snapshot = ""
        if mode_norm == "DELTA":
            snapshot = self._snapshot_page(url)

        latch_id = str(int(self.next_id))
        self.next_id = self.next_id + u256(1)

        record = LatchRecord(
            payer=gl.message.sender_address,
            recipient=Address(recipient),
            url=url.strip(),
            promise=promise.strip(),
            mode=mode_norm,
            snapshot=snapshot,
            amount=stake,
            deadline=deadline,
            status="OPEN",
            payout_bps=u256(0),
            evidence_quote="",
            reason="",
        )
        self.latches[latch_id] = record

    @gl.public.write
    def claim_done(self, latch_id: str):
        record = self.latches[latch_id]
        if gl.message.sender_address != record.recipient:
            raise Exception("only the recipient can claim")
        if record.status != "OPEN":
            raise Exception("latch is not open")
        record.status = "CLAIMED"
        self.latches[latch_id] = record

    @gl.public.write
    def adjudicate(self, latch_id: str):
        record = self.latches[latch_id]
        if record.status not in ("OPEN", "CLAIMED"):
            raise Exception("already settled")

        url = record.url
        promise = record.promise
        mode = record.mode
        snapshot = record.snapshot
        amount = record.amount
        payer = record.payer
        recipient = record.recipient

        def evaluate() -> str:
            page = gl.nondet.web.render(url, mode="text")
            excerpt = _norm_text(page, 8000)

            if mode == "DELTA":
                task = (
                    "A worker was paid to change a public webpage.\n"
                    "Compare the OPENING SNAPSHOT to the LIVE PAGE.\n"
                    "Decide if the PROMISE was actually fulfilled by a real change.\n"
                    "Ignore unrelated layout shifts, ads, timestamps, and cookies.\n"
                )
                extra = f"OPENING SNAPSHOT:\n{snapshot}\n\n"
            else:
                task = (
                    "Decide if the LIVE PAGE currently satisfies the PROMISE.\n"
                    "Judge only what is visible on the page. Do not use outside knowledge "
                    "except common sense about what the URL itself is.\n"
                )
                extra = ""

            prompt = (
                f"{task}"
                "Return JSON with keys:\n"
                '  verdict: HONOR | DENY | PARTIAL\n'
                "  payout_bps: integer 0-10000 (HONOR=10000, DENY=0, PARTIAL=your split)\n"
                "  evidence_quote: a short quote copied from the live page\n"
                "  reason: one or two sentences\n\n"
                f"PROMISE:\n{promise}\n\n"
                f"{extra}"
                f"LIVE PAGE:\n{excerpt}"
            )
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            parsed = _parse_verdict(raw)
            return json.dumps(parsed, sort_keys=True)

        result_json = gl.eq_principle.prompt_comparative(
            evaluate,
            principle=(
                "The `verdict` field MUST be identical. "
                "`payout_bps` MUST be within 500 basis points. "
                "evidence_quote and reason may differ in wording but must support the same verdict."
            ),
        )

        parsed = _parse_verdict(result_json)
        payout_bps = u256(int(parsed["payout_bps"]))
        to_recipient = (amount * payout_bps) // u256(10000)
        to_payer = amount - to_recipient

        self._credit(recipient, to_recipient)
        self._credit(payer, to_payer)

        record.status = parsed["verdict"]
        record.payout_bps = payout_bps
        record.evidence_quote = parsed["evidence_quote"]
        record.reason = parsed["reason"]
        self.latches[latch_id] = record

    @gl.public.write
    def withdraw(self):
        who = gl.message.sender_address
        amount = self.balances.get(who, u256(0))
        if amount == u256(0):
            raise Exception("nothing to withdraw")
        self.balances[who] = u256(0)
        who.emit_transfer(amount)

    @gl.public.view
    def get_latch(self, latch_id: str) -> dict:
        record = self.latches[latch_id]
        return {
            "payer": str(record.payer),
            "recipient": str(record.recipient),
            "url": record.url,
            "promise": record.promise,
            "mode": record.mode,
            "snapshot": record.snapshot,
            "amount": str(record.amount),
            "deadline": str(record.deadline),
            "status": record.status,
            "payout_bps": str(record.payout_bps),
            "evidence_quote": record.evidence_quote,
            "reason": record.reason,
        }

    @gl.public.view
    def get_balance(self, who: str) -> str:
        return str(self.balances.get(Address(who), u256(0)))

    @gl.public.view
    def get_next_id(self) -> str:
        return str(self.next_id)
