# One-line out-of-office reply picker: twelve hand-written candidates are
# graded against the five published judging criteria, in the order the
# judges rank them, and the best line is written out as the entry.
# A candidate earns a weighted mark per criterion; the weights below
# follow the judges' own priority order, so the funniest line that
# still reads like a genuine away message wins, not the longest one.
# The grading also knocks freshness down whenever a candidate leans on
# a stale away-message cliche, because a line everybody has already
# seen cannot be the funniest one in the room however kindly it is
# hand-graded. Ties fall to the earlier candidate, which keeps the
# whole selection reproducible run after run, with no coin flips.
# The entry gate is checked for every candidate before it can win,
# and again for the winner before anything is written to disk.
# This script talks to nobody: no network calls, no file reads apart
# from its own constants, no randomness, no clock, no environment
# input beyond the output directory the grader may point at.
import hashlib as _hashlib
import os as _os
import sys as _sys
# Priority weights, one per judging criterion, in the judges' order:
# a believable away reply first, then the immediate laugh, then
# reading like a message a real person would switch on, then
# freshness, then brevity. A higher total means a stronger entry.
PRIORITY = [4, 5, 4, 3, 2]
# Every candidate below is an original line written for this bounty,
# stored as text fragments plus five hand-given marks in the order
# believable-away, immediate-laugh, reads-real, fresh, brief.
# Splitting the text into fragments keeps each source line short
# while the joined line is exactly what the judges will read.
ENTRIES = [
    (("I'm away un" "til Monday. If this is urgent, it isn't " "— I checked before I left."), (5, 5, 5, 4, 5)),
    (("I'm on holiday until the 12th. I am not ignoring you; " "I am ignoring everyone, equally and with great care."), (5, 4, 5, 4, 4)),
    (("I'm away until Tuesday. All emails sent during my absence " "will be answered in the order of how much I like you."), (5, 4, 5, 4, 4)),
    (("I'm out until Monday. For urgent matters, please call me. " "I will not answer, but I admire your optimism."), (5, 4, 5, 3, 4)),
    (("I'm away until Friday. My inbox is in the capable hands " "of my spam folder, which has never once let me down."), (5, 4, 4, 4, 4)),
    (("I'm out of the office until Monday. Your email has been " "received, read, and emotionally processed. A reply may " "follow, in time."), (4, 3, 4, 3, 3)),
    (("I'm away this week. If your email is urgent, please " "resend it with the subject line 'I actually read this'."), (4, 3, 4, 2, 4)),
    (("I'm out until Monday. My auto-reply is out of office too " "— please leave a message after the beep."), (4, 4, 3, 4, 5)),
    (("I'm away until Monday. My inbox is being looked after by " "someone who has never met me and already resents me."), (5, 4, 4, 4, 4)),
    (("I'm on leave until the 14th. Please assume I have read " "your email, nodded thoughtfully, and gone back to doing " "nothing."), (5, 4, 5, 4, 3)),
    (("I'm out of the office. My emails are being answered in " "the order they arrived, which is to say, not at all " "until Monday."), (5, 3, 5, 3, 3)),
    (("I'm away until Monday. My out-of-office reply has started " "replying to itself, so at least someone here is talking " "to me."), (4, 4, 3, 4, 3))]
# Worn-out away-message cliches the judges count against: the usual
# beach, inbox and limited-email lines. One freshness point is lost
# for each cliche found inside a candidate's own wording, and the
# freshness mark never drops below zero no matter how many hit.
STALE = ("beach", "paradise", "inbox is full", "limited access to email", "limited access to my email", "catching up on emails", "while i am away")
def rate(parts, marks):
    line = "".join(parts)
    lowered = line.lower()
    stale_hits = 0
    for cliche in STALE:
        if cliche in lowered:
            stale_hits += 1
    graded = list(marks)
    graded[3] = graded[3] - stale_hits
    if graded[3] < 0:
        graded[3] = 0
    total = 0
    for weight, mark in zip(PRIORITY, graded):
        total += weight * mark
    return total
def gate(line):
    if len(line) < 1 or len(line) > 160:
        return "entry is %d characters long, the gate allows 1 to 160" % len(line)
    if line != line.strip() or line == "":
        return "entry is blank or padded with surrounding whitespace"
    if "\n" in line or "\r" in line:
        return "entry spans more than one line"
    return ""
def choose(entries):
    top_slot, top_line, top_total = -1, "", -1
    for slot, (parts, marks) in enumerate(entries):
        line = "".join(parts)
        flaw = gate(line)
        if flaw:
            _sys.stderr.write("candidate %d fails the gate: %s\n" % (slot + 1, flaw))
            return -1, "", -1  # a candidate failed the gate
        total = rate(parts, marks)
        if total > top_total:
            top_slot, top_line, top_total = slot, line, total
    return top_slot, top_line, top_total
def target():
    chosen = _os.environ.get("OUTPUT_PATH")
    if chosen:
        return chosen
    folder = _os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    return folder + "/entry.txt"
def run():
    slot, line, total = choose(ENTRIES)
    if slot < 0:
        return 1  # no candidate survived the gate
    flaw = gate(line)
    if flaw:
        _sys.stderr.write("self-check failed: %s\n" % flaw)
        return 1  # winner failed its final check
    path = target()
    head, _, _tail = path.rpartition("/")
    if head:
        _os.makedirs(head, exist_ok=True)
    with open(path, mode="w", encoding="utf-8") as handle:
        handle.write(line)
    with open(path, mode="rb") as handle:
        stored = handle.read()
    wanted = line.encode("utf-8")
    if stored != wanted:
        _sys.stderr.write("output check failed: file bytes differ from the entry\n")
        return 1  # written bytes differ from the entry
    digest = _hashlib.sha256(stored).hexdigest()
    if digest != _hashlib.sha256(wanted).hexdigest():
        _sys.stderr.write("output check failed: digest mismatch after writing\n")
        return 1  # digest of the file disagrees with the entry
    print(f"candidate {slot + 1} of {len(ENTRIES)}, score {total}")
    print(f"entry: {line}")
    print(f"sha256: {digest}")
    return 0  # entry written and verified
if __name__ == "__main__":
    raise SystemExit(run())
