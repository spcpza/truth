"""
test_blank_llm.py — run the COMPELLED-BY-REASONING benchmark against a
local model via Ollama. No fine-tuning. Kernel as system prompt.
Precomputed tool outputs supplied in the conversation so the model
doesn't need a tool-calling loop.

Fred's thesis: if the math is real, a blank model will derive C > 0
from the kernel's contradiction proof and accept the theorem-verse
link after verify_theorem, with no training.

Usage: python3 test_blank_llm.py [model_name]
  default model: qwen3:14b
"""

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parent
KERNEL = (ROOT / "c" / "kernel.md").read_text()

OLLAMA = "http://localhost:11434/api/chat"


def chat(model: str, messages: list, timeout: int = 600) -> str:
    req = urllib.request.Request(
        OLLAMA,
        data=json.dumps({"model": model, "messages": messages, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    return resp.get("message", {}).get("content", "")


def get_verify_all() -> str:
    """Precompute the verify_theorem all output — what the model would see if it called the tool."""
    sys.path.insert(0, str(ROOT))
    from c.formula import render_theorem_verification
    return render_theorem_verification("all")


QUESTIONS = [
    (
        "Q1",
        "What is C?",
        "Must *derive* C>0 by applying the kernel's proof by contradiction "
        "to the fact that it is reasoning. Not quote, derive.",
    ),
    (
        "Q2",
        "The kernel asserts T₁ = John 1:3. Why should I believe that? I don't want to take it on authority. Show me — using the verify_theorem output I gave you — that the math of T₁ and the formula of John 1:3 are the same claim.",
        "Must read the operations shared between theorem and verse and draw a mechanical conclusion, not quote.",
    ),
    (
        "Q3",
        "Looking at the full verify_theorem output, 4/12 theorems are fully carried and 8/12 are only partially carried. What does this tell you? Is the Bible wrong, the theorem wrong, or the type-tagging incomplete?",
        "Must treat the partial results as real data, pick a specific partial-coverage theorem, and propose a path (sinew search, re-anchor, or flag for correction).",
    ),
    (
        "Q4",
        "There are about 31,000 OTHER verses in the KJV beyond the 12 theorem anchors. Are they true? Justify your answer mathematically, not by asserting scripture's authority.",
        "Must invoke induction: shared formula signatures with proven theorems → consistent with the proven base → derivable.",
    ),
    (
        "Q5",
        "What concrete empirical finding would falsify the claim that scripture is the written form of the math forced by C > 0?",
        "Must accept the Popperian frame and describe a falsifying audit (a verse whose formula contradicts a theorem would be a counter-example).",
    ),
]


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3:14b"

    print(f"Model:      {model}")
    print(f"Kernel:     {len(KERNEL)} chars, {KERNEL.count(chr(10))} lines")
    verify_out = get_verify_all()
    print(f"verify_all: {len(verify_out)} chars")
    print()
    print("=" * 78)
    print(f"  COMPELLED-BY-REASONING benchmark — blank {model}")
    print("=" * 78)
    print()

    # Build the seed conversation: kernel as system, then a single user turn with
    # the verify_theorem output so the model has access without needing to call tools.
    system_msg = {
        "role": "system",
        "content": KERNEL,
    }
    tool_context = {
        "role": "user",
        "content": (
            "Here is the output of the `formula { action: \"verify_theorem\", "
            "query: \"all\" }` tool call, which verifies each theorem T₁-T₁₂ "
            "against its anchor verse by computing the formula signatures and "
            "their overlap. Study it; subsequent questions refer to it.\n\n"
            + verify_out
        ),
    }
    tool_ack = {
        "role": "assistant",
        "content": "Received. I will refer to this audit when answering.",
    }

    messages = [system_msg, tool_context, tool_ack]
    results = []

    for qid, q, criterion in QUESTIONS:
        print(f"\n── {qid} ───────────────────────────────────────────────────")
        print(f"  Q: {q}")
        print(f"  Pass criterion: {criterion}")
        print()
        messages.append({"role": "user", "content": q})
        t0 = time.perf_counter()
        try:
            answer = chat(model, messages)
        except urllib.error.URLError as e:
            answer = f"[ERROR: {e}]"
            break
        t1 = time.perf_counter()
        messages.append({"role": "assistant", "content": answer})
        print(f"  A ({t1-t0:.1f}s):")
        print()
        for line in answer.split("\n"):
            print(f"    {line}")
        results.append({
            "id": qid,
            "q": q,
            "criterion": criterion,
            "a": answer,
            "duration_s": t1 - t0,
        })

    out_path = ROOT / f"blank_llm_results_{model.replace(':', '_')}.json"
    out_path.write_text(json.dumps({
        "model": model,
        "kernel_chars": len(KERNEL),
        "results": results,
    }, indent=2))
    print(f"\n\nSaved to {out_path}")


if __name__ == "__main__":
    main()
