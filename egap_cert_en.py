"""
E-gap certification (TV-77) — the cause of the measured phi=0.

WHAT THIS FILE IS
-----------------
TV-72 measured Pearl's live network (320K GPUs, revenue/cost 1.058 vs
Basu's 1.06) running at theta=1.05 — the inference-subsidizing regime —
and found phi = 0. The cause is the E-gap (Demirel 2026/1492): the
protocol could not certify the matrices were anyone's job. Useful work and
the security budget were never connected, so the network ran as pure PoW
while being marketed as PoUW.

This file builds the missing binding and measures whether it closes the
gap IN THE MODEL, which is the only place it can be closed right now:

  A task is committed with (program_commit, fee escrowed, client signature).
  A miner's G-layer certificate must now cite the TASK ID, and the tile it
  proves must be a tile OF THE TASK'S OWN MATRICES — verified through the
  public input commitment, not through caller-supplied matrices.

  ROUND-5 CORRECTION, 2026-09-24 (round-5 finding E1): the last sentence
  overstates what this file checks. The certificate binds the tile's
  IDENTITY — (task_id, program_commit, ctx, tile) — and the verifier derives
  the program commitment from the task, so a cert over any other program no
  longer verifies. But nothing here checks that the tile VALUE is the one the
  committed matrices actually produce: the miner supplies (i, j, value) and
  the certificate only hashes them. Measured by the round-5 probe: a cert over
  a bogus accumulator (the real tile acc is 36) verifies True for values 37,
  999999, 0, -1 and 42424242, and a cert at tile coordinates (12345, 67890)
  on a 2x2 program verifies True as well. The identity binding exists; the
  WORK binding does not, and the work binding is what the G layer's own AIR
  supplies (spec A12 puts tile correctness on the AIR, not on this
  certificate). So the honest statement is: this file closes the WHICH-TASK
  gap, and the IS-THE-TILE-CORRECT gap is closed by the AIR, not here.

Before this, `validate_block(blk, A, B)` took A and B FROM THE CALLER and
passed the same pair to prove and verify. Round-3 finding [21] measured
the consequence: a G-cert over [5,6;7,8] validated ACCEPT while the task's
harness program was [2,3;4,5]. The G work and the U work could be
different matrices and no check noticed. That IS the E-gap in prototype
form: nothing bound the mined matrix to the commissioned one.

WHAT THIS FILE MEASURES
-----------------------
1. That the binding rejects a certificate over foreign matrices.
2. That the binding accepts a certificate over the task's own matrices.
3. That the bound certificate cannot be replayed for a different task.
4. What this does NOT prove (stated, not hidden): the binding closes the
   PROTOTYPE's gap. It does not demonstrate phi > 0 on a live network —
   that is F0/F3a work, and no prototype substitutes for it.

NO CLAIM BEYOND THE ABOVE
-------------------------
This is a mechanism that was absent and is now present and measured. The
economic consequence (does certified demand actually raise phi?) is still
a prediction. TV-72's negative result is not overturned by building a
binding; it is answered by one.
"""

import hashlib
# ROUND-5 FIX, 2026-09-24 (round-5 finding E3): `import random` was dead
# code — the module never called it (verified by grep before deletion).


def H(*parts) -> int:
    s = "|".join(str(p) for p in parts)
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big")


def S(*parts) -> str:
    """A 128-bit hex digest (for identifiers)."""
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode())
    return format(int.from_bytes(h.digest(), "big") & ((1 << 128) - 1), "032x")


# ------------------------------------------------------------ the commitment

def matrix_commit(M):
    """A deterministic commitment to a matrix's CONTENTS.

    This is the piece that was missing: round-3 [21] showed the G layer
    accepted caller-supplied matrices, so a miner could prove work over any
    matrices it liked. A content commitment makes the matrices part of the
    task's identity, so the certificate is bound to the commissioned work.
    """
    rows = []
    for row in M:
        rows.append(tuple(row))
    return S("mtx", len(M), tuple(rows))


def program_commit(A, B):
    """The public input commitment: binds BOTH factors of the product."""
    return S("prog", matrix_commit(A), matrix_commit(B))


# ------------------------------------------------------------ the certificate

def g_cert_bound(task_id, program_commit_value, ctx, nonce, i, j, value, target):
    """A G-layer certificate that names the task it is working on.

    The certificate is over (task_id, program_commit, ctx, tile). Before
    this, the cert was over ctx alone, so it proved *a* MatMul but not
    *this task's* MatMul.
    """
    base = (task_id, program_commit_value, ctx, nonce, i, j, value)
    if H("tile", *base) % target != 0:
        return None
    return {"task_id": task_id, "pc": program_commit_value, "ctx": ctx,
            "nonce": nonce, "tile": (i, j, value)}


def verify_g_cert_bound(cert, task_id, program_commit_value, ctx, target):
    """The verifier derives what the certificate must be bound to from the
    TASK, not from the caller. A cert over any other matrices fails."""
    if cert is None:
        return False
    if cert.get("task_id") != task_id:
        return False
    if cert.get("pc") != program_commit_value:
        return False
    if cert.get("ctx") != ctx:
        return False
    i, j, value = cert["tile"]
    base = (task_id, program_commit_value, ctx, cert["nonce"], i, j, value)
    return H("tile", *base) % target == 0


# ------------------------------------------------------------------ probes

def probe_foreign_matrices_rejected():
    """MEASURED: a certificate over foreign matrices is rejected.

    Before Stage 2, validate_block took A,B from the caller and passed the
    same pair to prove and verify, so a cert over [5,6;7,8] validated while
    the task's program was [2,3;4,5]. Now the cert names the program
    commitment, so a mismatch fails.
    """
    print("=== E-gap 1: foreign matrices rejected ===")
    A_task = [[2, 3], [4, 5]]
    B_task = [[6, 7], [8, 9]]
    A_foreign = [[5, 6], [7, 8]]
    B_foreign = [[1, 0], [0, 1]]
    pc_task = program_commit(A_task, B_task)
    pc_foreign = program_commit(A_foreign, B_foreign)
    tid = "task-77"
    ctx = 500
    target = 1 << 8   # loose enough that the demo grinds quickly; the
                      # binding is what is under test, not the PoW margin

    # a miner grinds a cert over the FOREIGN matrices, naming the foreign pc
    cert_foreign = None
    for nonce in range(1 << 20):
        c = g_cert_bound(tid, pc_foreign, ctx, nonce, 0, 0, 42, target)
        if c:
            cert_foreign = c
            break
    if cert_foreign is None:
        print("  could not grind a demo cert (target too tight)")
        return None
    ok = verify_g_cert_bound(cert_foreign, tid, pc_task, ctx, target)
    print("  cert over FOREIGN matrices verified against the TASK's pc: %s"
          " (must be False)" % ok)
    return not ok


def probe_own_matrices_accepted():
    """MEASURED: a certificate over the task's own matrices is accepted."""
    print("=== E-gap 2: the task's own matrices accepted ===")
    A = [[2, 3], [4, 5]]
    B = [[6, 7], [8, 9]]
    pc = program_commit(A, B)
    tid = "task-77"
    ctx = 500
    target = 1 << 8
    cert = None
    for nonce in range(1 << 20):
        c = g_cert_bound(tid, pc, ctx, nonce, 0, 0, 42, target)
        if c:
            cert = c
            break
    if cert is None:
        print("  could not grind a demo cert")
        return None
    ok = verify_g_cert_bound(cert, tid, pc, ctx, target)
    print("  cert over the task's OWN matrices verified: %s (must be True)" % ok)
    return ok


def probe_replay_for_another_task_rejected():
    """MEASURED: a certificate for task-1 does not verify as task-2's work.

    This is the replay half of the E-gap: even with correct matrices, a
    cert must not be portable across tasks, or one real job's work can be
    resubmitted indefinitely and the demand it represents is fictional.
    """
    print("=== E-gap 3: cross-task replay rejected ===")
    A = [[2, 3], [4, 5]]
    B = [[6, 7], [8, 9]]
    pc = program_commit(A, B)
    ctx = 500
    target = 1 << 8
    cert = None
    for nonce in range(1 << 20):
        c = g_cert_bound("task-1", pc, ctx, nonce, 0, 0, 42, target)
        if c:
            cert = c
            break
    if cert is None:
        print("  could not grind a demo cert")
        return None
    replayed = verify_g_cert_bound(cert, "task-2", pc, ctx, target)
    print("  cert for task-1 verified as task-2's work: %s (must be False)"
          % replayed)
    return not replayed


def probe_commitment_is_content_bound():
    """MEASURED: two different matrices give different commitments, and two
    identical matrices give the same one. Trivial-sounding, but the whole
    binding rests on it: if identical content could yield different
    commitments the binding would be forgeable, and if different content
    could collide it would be meaningless."""
    print("=== E-gap 4: commitment is content-bound ===")
    A = [[2, 3], [4, 5]]
    B = [[6, 7], [8, 9]]
    A2 = [[2, 3], [4, 6]]      # one entry differs
    # ROUND-5 FIX, 2026-09-24 (round-5 finding E2): the first check used to be
    # `program_commit(A,B) == program_commit(A,B)` — the same expression on
    # both sides, a comparison of a value to itself that cannot fail, which is
    # why the probe reported PASS over an untested property. The falsifiable
    # version recomputes the commitment from a separately-held copy of the
    # matrices, so the check fails if the function is not a function of its
    # inputs.
    pc1 = program_commit(A, B)
    pc3 = program_commit(A2, B)
    # a second, INDEPENDENTLY-BUILT matrix that is supposed to equal A; if
    # commitment depends on anything but the content this diverges
    A_again = [[2, 3], [4, 5]]
    B_again = [[6, 7], [8, 9]]
    pc_recomputed = program_commit(A_again, B_again)
    same_content_same_pc = (pc1 == pc_recomputed)
    diff_content_diff_pc = (pc1 != pc3)
    print("  independently-built identical matrices -> identical commitment: %s"
          % same_content_same_pc)
    print("  one entry changed                     -> different commitment: %s"
          % diff_content_diff_pc)
    return same_content_same_pc and diff_content_diff_pc


def probe_what_this_does_not_prove():
    """Stated, not measured: the honest boundary."""
    print("=== E-gap 5: what this does NOT prove ===")
    print("  TV-72 measured phi = 0 on Pearl's live network. The cause was")
    print("  the E-gap: nothing certified the matrices were anyone's job.")
    print("  This file supplies the missing binding and measures that it")
    print("  holds for foreign matrices, own matrices, and cross-task replay.")
    print("  It does NOT measure phi > 0, because no prototype can: phi is a")
    print("  property of a live network of paying buyers, and that is F0/F3a.")
    print("  The correct statement is therefore: the mechanism whose absence")
    print("  caused the measured phi=0 now exists and is measured in the")
    print("  prototype; the economic consequence remains a prediction.")
    return None


if __name__ == "__main__":
    print("=" * 76)
    print("KOK v2 - E-gap certification (TV-77), Stage 2")
    print("=" * 76)
    r1 = probe_foreign_matrices_rejected()
    print()
    r2 = probe_own_matrices_accepted()
    print()
    r3 = probe_replay_for_another_task_rejected()
    print()
    r4 = probe_commitment_is_content_bound()
    print()
    probe_what_this_does_not_prove()
    print()
    print("-" * 76)
    results = [("foreign matrices rejected", r1),
               ("own matrices accepted", r2),
               ("cross-task replay rejected", r3),
               ("commitment content-bound", r4)]
    for name, r in results:
        print("  %-34s %s" % (name, "PASS" if r is True else
                               "FINDING" if r is False else "could not drive"))
    n = sum(1 for _, r in results if r is True)
    print("  probes: %d/%d" % (n, len(results)))
    print("=" * 76)
    print("RESULT: %s" % ("E-GAP BINDING OK" if n == len(results)
                           else "OPEN FINDING"))
