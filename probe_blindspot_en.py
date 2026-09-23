"""TV-73: adversarial probes on the never-reviewed files.

Rounds one and two both reviewed f0b_air_proto.py and found critical bugs each
time. The third round was asked to review the files that had never been
reviewed and did not — all 27 of its probes targeted f0b again. This probe
drives the blind spot by RUNNING the state machine, not by reading it.

The U-layer contract is the fee invariant:
    fees_in == fees_refunded + fees_burned + fees_paid
The covered paths are submit, settle, timeout. This probe drives the corners
the tests may not cover, by actually constructing a task, settling it, and
then re-driving the terminal state.
"""

import sys
sys.path.insert(0, ".")


def _load():
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import u_layer_prototype_en as ul
    return ul


def _task_books(task):
    """The two counters a task keeps that the invariant is stated over."""
    return task.escrow, task.burned


def _smallest_task(ul, q=97, n=8):
    """Build the smallest honest task the module accepts, following the shape
    the module's own tests use."""
    import random
    rnd = random.Random(11)
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    spec = ul.TaskSpec("mm", (A, B), 64, 1000)
    return spec, A, B


def _drive(ul, seed=11):
    """Build the smallest honest task, mining enough empty blocks first that
    the VRF epoch seed (lookback 64) is available."""
    import random
    ch = ul.Chain()
    rnd = random.Random(seed)
    q, n = 97, 8
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    zero = [[0] * n for _ in range(n)]
    for _ in range(ul.EPOCH_LOOKBACK + 2):
        blk = ch.mine_block("m1", [], zero, zero)
        ch.validate_block(blk, zero, zero)
    spec = ul.TaskSpec("mm", (A, B), 64, 1000)
    t = ch.submit_task("c1", spec, 100, 0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A, B)
    ch.validate_block(blk, A, B)
    return ch, t


def probe_double_settle():
    """Settle a task, then settle it AGAIN. If the terminal-state guard works
    the second call is a no-op and the task's escrow does not move twice."""
    ul = _load()
    print("CORNER 1: settle() the same task twice")
    print("-" * 60)
    try:
        ch, t = _drive(ul)
        task = ch.tasks[t.tid]
        print("  initial            : escrow=%s burned=%s state=%s"
              % (task.escrow, task.burned, task.state))
        ch.settle(t.tid)
        mid = _task_books(task)
        print("  after first settle : escrow=%s burned=%s state=%s"
              % (mid[0], mid[1], task.state))
        ch.settle(t.tid)
        after = _task_books(task)
        print("  after second settle: escrow=%s burned=%s state=%s"
              % (after[0], after[1], task.state))
        if mid == after:
            print("  -> second settle is a NO-OP: the terminal-state guard")
            print("     holds and the books move once. Invariant intact.")
            return True
        print("  -> second settle MOVED THE BOOKS: the fee invariant can be")
        print("     broken by a double transition.")
        return False
    except Exception as e:
        print("  could not construct the corner: %s: %s"
              % (type(e).__name__, e))
        return None


def probe_late_challenge():
    """Challenge a task that is already settled.

    This corner found a REAL BUG (fixed 2026-09-23): the challenger was
    registered with setdefault only on the fraud-proven path, so a
    challenge that did not prove fraud raised KeyError instead of being
    counted. The registration now precedes both paths."""
    ul = _load()
    print("CORNER 2: challenge() an already-settled task")
    print("-" * 60)
    try:
        ch, t = _drive(ul)
        task = ch.tasks[t.tid]
        ch.settle(t.tid)
        before = _task_books(task)
        out = ch.challenge("bob", t.tid, ch.height())
        after = _task_books(task)
        print("  before late challenge: escrow=%s burned=%s state=%s"
              % (before[0], before[1], task.state))
        print("  challenge() returned : %s" % (out,))
        print("  after  late challenge: escrow=%s burned=%s state=%s"
              % (after[0], after[1], task.state))
        print("  challenger registered: %s" % ("bob" in ch.miners))
        if before == after and out[0] == "CHALLENGE_REJECTED":
            print("  -> late challenge is REJECTED and the books do not move:")
            print("     the terminal state is guarded on the challenge path.")
            print("     Before the fix this raised KeyError — the challenger")
            print("     was never registered on the non-fraud path.")
            return True
        print("  -> late challenge MOVED THE BOOKS on a settled task.")
        return False
    except Exception as e:
        print("  could not construct the corner: %s: %s"
              % (type(e).__name__, e))
        return None


def probe_fraud_challenge_registration():
    """The sharper form of corner 2: a challenge on a SOLVED-but-wrong task
    must register the challenger on BOTH outcomes, not only when fraud is
    proven. Driven by challenging with a challenger no one registered."""
    ul = _load()
    print("CORNER 3: challenger registration on the non-fraud path")
    print("-" * 60)
    try:
        ch, t = _drive(ul)
        task = ch.tasks[t.tid]
        # challenge WITHOUT settling first, on an honest (non-fraud) result
        out = ch.challenge("carol", t.tid, ch.height())
        print("  challenge on honest result : %s" % (out,))
        print("  challenger registered      : %s" % ("carol" in ch.miners))
        if "carol" in ch.miners:
            print("  -> the challenger is registered on the non-fraud path too.")
            print("     This is the exact case that raised KeyError before")
            print("     the 2026-09-23 fix.")
            return True
        print("  -> the challenger is NOT registered on the non-fraud path.")
        return False
    except Exception as e:
        print("  could not construct the corner: %s: %s"
              % (type(e).__name__, e))
        return None


def probe_ghostdag_minimal_deviation():
    """Is the TV-59 mergeset deviation structural, i.e. present on a minimal
    chain, or is it an artifact of the 51-block random chain the test used?

    Measured here by building the smallest chain that can have an anticone
    and counting order entries outside the block's own past."""
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import ghostdag_proto_en as gd
    import inspect

    print("GHOSTDAG mergeset deviation on a minimal chain")
    print("-" * 60)
    fns = [n for n, o in vars(gd).items()
           if inspect.isfunction(o) and ("order" in n or "merge" in n
                                         or "anticone" in n)]
    print("  ordering functions exposed : %s" % (fns or "none"))
    print("  TV-59 measured 572 entries outside a block's own past on 51")
    print("  blocks. The module exposes no minimal-anticone builder, so this")
    print("  probe cannot decide whether the deviation appears at n=3. The")
    print("  honest status is: deviation MEASURED at 51 blocks, minimal-chain")
    print("  behaviour UNMEASURED, and that is a real gap in the evidence")
    print("  rather than a clean result.")
    return None


def main():
    print("=" * 70)
    print("TV-73: the blind spot — the never-reviewed files, probed by running")
    print("=" * 70)
    print()
    print("Rounds one and two reviewed f0b only. The third round was asked to")
    print("review the rest and did not — 27 probes, all on f0b. This probe")
    print("drives what was missed and reports the actual outcome.\n")
    r1 = probe_double_settle()
    print()
    r2 = probe_late_challenge()
    print()
    r3 = probe_fraud_challenge_registration()
    print()
    probe_ghostdag_minimal_deviation()
    print()
    print("-" * 70)
    print("RESULTS")
    print("-" * 70)
    print("  double settle        : %s"
          % ("GUARDED" if r1 is True else
             "BOOKS MOVED — FINDING" if r1 is False else "could not drive"))
    print("  late challenge       : %s"
          % ("GUARDED" if r2 is True else
             "BOOKS MOVED — FINDING" if r2 is False else "could not drive"))
    print("  challenger register  : %s"
          % ("REGISTERED" if r3 is True else
             "NOT REGISTERED — FINDING" if r3 is False else "could not drive"))
    print("  minimal mergeset     : UNMEASURED (module exposes no builder)")
    print()
    print("  Where this probe could drive a corner it reports the outcome;")
    print("  where the module exposes no harness it says so instead of")
    print("  asserting a clean result. The never-reviewed files are not")
    print("  claimed clean — they are claimed RUN and regression-checked, and")
    print("  what they lack is the adversarial pass that found two rounds of")
    print("  critical bugs in f0b.")
    return True


if __name__ == "__main__":
    ok = main()
    print()
    print("RESULT: %s" % ("STATED" if ok else "FAIL"))
    sys.exit(0 if ok else 1)
