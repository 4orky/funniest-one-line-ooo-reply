#!/usr/bin/env python3
"""Funniest one-line out-of-office reply.

Writes a single original out-of-office auto-reply to
/output/entry.txt. The sealed gate wants UTF-8 text of 1 to 160
characters, one line, not only whitespace.

How the line is chosen: twelve original candidates, each written for
this bounty, are rated 0-5 on the judge's five criteria, in the
judge's own order of importance:

  1. it is a one-line out-of-office reply, the sort a person sets
     before going away
  2. the laugh lands on the first read, with no setup and nothing to
     explain afterwards
  3. it still reads like a real away message a person would be glad
     to switch on, not a notice with a joke bolted to it
  4. the joke is fresh: a turn on the usual away message rather than
     the same beach, inbox or limited-email lines
  5. it is short enough to take in at a glance, with every word
     earning its place

Each criterion carries a weight (4, 5, 4, 3, 2) matching that order.
The highest weighted total wins; ties go to the earliest candidate,
so the choice is fully deterministic. Freshness is not only
hand-rated: any candidate leaning on a tired away-message trope
loses one freshness point per trope phrase found in its own text,
so a line everyone has already heard cannot win on a generous hand
rating alone. Every candidate is checked against the gate before it
can be picked, not just the winner. No network, no external input,
no randomness. The program checks its own output against the gate
before writing it, and prints the SHA-256 of the file it wrote.
"""

from hashlib import sha256
from os import environ, makedirs
from sys import exit as done, stderr

# Weights for the five judge criteria, in the judge's priority order:
# a real away message, instant laugh, reads like a real message,
# fresh, short.
WEIGHTS = (4, 5, 4, 3, 2)

# Each candidate: (text, (real-away, instant-laugh, real-message,
# fresh, short)). All twelve lines are original, written for this
# entry, and each one is 1-160 characters, a single line.
CANDIDATES = [
    (
        "I'm away until Monday. If this is urgent, it isn't "
        "\u2014 I checked before I left.",
        (5, 5, 5, 4, 5),
    ),
    (
        "I'm on holiday until the 12th. I am not ignoring you; "
        "I am ignoring everyone, equally and with great care.",
        (5, 4, 5, 4, 4),
    ),
    (
        "I'm away until Tuesday. All emails sent during my absence "
        "will be answered in the order of how much I like you.",
        (5, 4, 5, 4, 4),
    ),
    (
        "I'm out until Monday. For urgent matters, please call me. "
        "I will not answer, but I admire your optimism.",
        (5, 4, 5, 3, 4),
    ),
    (
        "I'm away until Friday. My inbox is in the capable hands "
        "of my spam folder, which has never once let me down.",
        (5, 4, 4, 4, 4),
    ),
    (
        "I'm out of the office until Monday. Your email has been "
        "received, read, and emotionally processed. A reply may "
        "follow, in time.",
        (4, 3, 4, 3, 3),
    ),
    (
        "I'm away this week. If your email is urgent, please "
        "resend it with the subject line 'I actually read this'.",
        (4, 3, 4, 2, 4),
    ),
    (
        "I'm out until Monday. My auto-reply is out of office too "
        "\u2014 please leave a message after the beep.",
        (4, 4, 3, 4, 5),
    ),
    (
        "I'm away until Monday. My inbox is being looked after by "
        "someone who has never met me and already resents me.",
        (5, 4, 4, 4, 4),
    ),
    (
        "I'm on leave until the 14th. Please assume I have read "
        "your email, nodded thoughtfully, and gone back to doing "
        "nothing.",
        (5, 4, 5, 4, 3),
    ),
    (
        "I'm out of the office. My emails are being answered in "
        "the order they arrived, which is to say, not at all "
        "until Monday.",
        (5, 3, 5, 3, 3),
    ),
    (
        "I'm away until Monday. My out-of-office reply has started "
        "replying to itself, so at least someone here is talking "
        "to me.",
        (4, 4, 3, 4, 3),
    ),
]


# Worn-out away-message tropes the judge explicitly counts against:
# the same beach, inbox or limited-email lines. A candidate leaning
# on one of these has already been told a thousand times, so each hit
# costs one freshness point (freshness clamped at zero).
TIRED_PHRASES = (
    "beach",
    "limited access to email",
    "limited access to my email",
    "catching up on emails",
    "paradise",
    "inbox is full",
    "while i am away",
)


def score(text, ratings):
    """Weighted total for one candidate's five criterion ratings.

    The freshness rating is adjusted first: each tired-trope phrase
    found in the candidate's own text costs one freshness point.
    """
    real_away, laugh, real_message, fresh, short = ratings
    lowered = text.lower()
    hits = sum(1 for phrase in TIRED_PHRASES if phrase in lowered)
    fresh = max(0, fresh - hits)
    adjusted = (real_away, laugh, real_message, fresh, short)
    return sum(weight * mark for weight, mark in zip(WEIGHTS, adjusted))


def pick(candidates):
    """Return (index, text, total) of the best candidate.

    Deterministic: only a strictly greater total replaces the
    leader, so the earliest candidate wins any tie.
    """
    best_index, best_text, best_total = -1, "", -1
    for index, (text, ratings) in enumerate(candidates):
        problem = check_gate(text)
        if problem is not None:
            print("candidate %d fails the gate: %s" % (index + 1, problem),
                  file=stderr)
            return -1, "", -1
        total = score(text, ratings)
        if total > best_total:
            best_index, best_text, best_total = index, text, total
    return best_index, best_text, best_total


def check_gate(text):
    """Check the chosen line the way the sealed scorer does."""
    if not 1 <= len(text) <= 160:
        return "length %d is outside 1..160 characters" % len(text)
    if text.strip() != text or not text.strip():
        return "entry is blank or has surrounding whitespace"
    if "\n" in text or "\r" in text:
        return "entry is not a single line"
    return None


def output_path():
    """Where the entry goes: the grader's output dir, else default."""
    out_dir = environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    if environ.get("OUTPUT_PATH"):
        return environ["OUTPUT_PATH"]
    return out_dir + "/entry.txt"


def main():
    index, text, total = pick(CANDIDATES)
    if index < 0:
        return 1
    problem = check_gate(text)
    if problem is not None:
        print("self-check failed: %s" % problem, file=stderr)
        return 1

    path = output_path()
    folder = path.rsplit("/", 1)[0] if "/" in path else ""
    if folder:
        makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    digest = sha256(text.encode("utf-8")).hexdigest()
    print("candidate %d of %d, score %d" % (index + 1, len(CANDIDATES), total))
    print("entry: %s" % text)
    print("sha256: %s" % digest)
    return 0


done(main())
