#!/usr/bin/env python3
"""Arithmetic for the capacity scale: home 12 cookies, each guest at least 6, pack of 8.

Two different staircases live here, and conflating them is the mistake worth avoiding:

  capacity(k) — the most guests that k bought packs can serve. Pack 8 > portion 6, so every
                extra pack raises capacity by at least one, which is why "one more pack" is
                always enough for one more guest in the range this file covers.
  k(N)        — the fewest packs that serve N guests, i.e. the first k with capacity(k) >= N.

"this pack added no capacity" is a statement about capacity(k); "a guest arrived and the purchase
did not change" is a statement about k(N). They are not the same event and do not happen at the
same k.

Run with --check to assert every published number and the invariants behind the captions.
"""
HOME = 12
MIN_PER_GUEST = 6
PACK = 8
MAX_GUESTS = 12


def capacity(k: int) -> int:
    """Most guests served by k packs: floor((home + PACK*k) / MIN_PER_GUEST)."""
    if k < 0:
        raise ValueError("k must be >= 0")
    return (HOME + PACK * k) // MIN_PER_GUEST


def k_for(n: int) -> int:
    """Fewest packs serving n guests."""
    if n < 1:
        raise ValueError("n must be >= 1 (n = 0 is out of the contract: no division by zero)")
    k = 0
    while capacity(k) < n:
        k += 1
    return k


def packs_word(k: int) -> str:
    """Accusative, for "Купить k ...": 1 пачку, 2-4 пачки, 5+ пачек."""
    n = k % 100
    if 11 <= n <= 14:
        return "пачек"
    n = k % 10
    if n == 1:
        return "пачку"
    if 2 <= n <= 4:
        return "пачки"
    return "пачек"


def packs_nom(k: int) -> str:
    """Nominative, for "итого k ...": 1 пачка, 2-4 пачки, 5+ пачек.

    The packs count is written in digits and the noun after it follows the numeral, not the verb:
    "итого 1 пачка", where a verb would demand "итого 1 пачку". The forms differ exactly at one,
    which is why one helper was not enough.
    """
    n = k % 100
    if 11 <= n <= 14:
        return "пачек"
    n = k % 10
    if n == 1:
        return "пачка"
    if 2 <= n <= 4:
        return "пачки"
    return "пачек"


def packs_gen(k: int) -> str:
    """Genitive, for "хватало k ...": 1 пачки, 2-4 пачки, 5+ пачек."""
    n = k % 100
    if 11 <= n <= 14:
        return "пачек"
    n = k % 10
    if n == 1:
        return "пачки"
    if 2 <= n <= 4:
        return "пачки"
    return "пачек"


def guests_word(n: int) -> str:
    n100 = n % 100
    if 11 <= n100 <= 14:
        return "гостей"
    n10 = n % 10
    if n10 == 1:
        return "гостя"
    if 2 <= n10 <= 4:
        return "гостей"
    return "гостей"


def row(n: int) -> dict:
    """Everything one position of the scale shows. No history is used."""
    k = k_for(n)
    cap = capacity(k)
    prev_guests = None if k == 0 else n - 1
    prev_k = None if k == 0 else k_for(n - 1)
    if k == 0:
        purchase = "Покупать не нужно"
        note = (
            f"Двенадцати домашних печений хватает на {capacity(0)} {guests_word(capacity(0))}; "
            f"пачка не нужна."
        )
    else:
        purchase = f"Купить {k} {packs_word(k)}"
        if prev_k == k:
            note = (
                f"Покупка не меняется: {k} {packs_nom(k)} нужно и на {n}, "
                f"и на {prev_guests} {guests_word(prev_guests)}."
            )
        else:
            had = "хватало домашних печений" if prev_k == 0 else f"хватало {prev_k} {packs_gen(prev_k)}"
            note = (
                f"Порог: на {prev_guests} {guests_word(prev_guests)} {had}. "
                f"Ещё одна пачка — итого {k} {packs_nom(k)}; "
                f"итог назван целиком, держать прошлое в голове не нужно."
            )
    return {
        "guests": n,
        "packs": k,
        "capacity": cap,
        "purchase": purchase,
        "coverage": f"С этой покупкой хватит до {cap} {guests_word(cap)}",
        "note": note,
        "covers": list(range(1, cap + 1)),
        "is_threshold": k > 0 and prev_k != k,
    }


# The author's own published expectations, transcribed from their message.
PUBLISHED = {2: (0, 2), 3: (1, 3), 4: (2, 4), 5: (3, 6), 6: (3, 6), 7: (4, 7)}


def main() -> int:
    import argparse, json

    ap = argparse.ArgumentParser(description="capacity scale arithmetic")
    ap.add_argument("--check", action="store_true", help="assert every published number")
    ap.add_argument("--json", metavar="PATH", help="write the whole table for the page builder")
    a = ap.parse_args()

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump([row(n) for n in range(1, MAX_GUESTS + 1)], fh, ensure_ascii=False, indent=1)
        print(f"wrote {a.json}")

    if not a.check:
        for n in range(1, MAX_GUESTS + 1):
            r = row(n)
            print(f"N={n:2}  k={r['packs']}  cap={r['capacity']:2}  {r['purchase']:<18} {r['note']}")
        return 0

    bad = []
    for n, (k, cap) in PUBLISHED.items():
        if k_for(n) != k:
            bad.append(f"N={n}: packs {k_for(n)} != published {k}")
        if capacity(k) != cap:
            bad.append(f"N={n}: capacity({k}) {capacity(k)} != published {cap}")

    # Invariants the captions rest on. If any of these fails, the words are wrong even though
    # the numbers may still add up.
    for n in range(1, MAX_GUESTS + 1):
        k = k_for(n)
        if k > 0 and capacity(k - 1) >= n:
            bad.append(f"N={n}: k={k} is not minimal, capacity({k-1})={capacity(k-1)} >= {n}")
        if capacity(k) < n:
            bad.append(f"N={n}: k={k} does not cover {n}")
        if k > 0 and k_for(n) - k_for(n - 1) > 1:
            bad.append(f"N={n}: pack jump {k_for(n-1)} -> {k} — 'one more pack' would be wrong")
        if row(n)["capacity"] < n:
            bad.append(f"N={n}: the highlighted range does not include the chosen guest count")

    # The distinction the author drew: marginal packs vs marginal guests.
    marginal = [capacity(k) - capacity(k - 1) for k in range(1, 9)]
    zero_return = [i + 1 for i, d in enumerate(marginal) if d == 0]  # empty when pack > portion
    thin = [(k, (HOME + 3 * k) // MIN_PER_GUEST) for k in range(0, 6)]
    print("N     k(N)  capacity(k(N))")
    for n in range(1, MAX_GUESTS + 1):
        r = row(n)
        print(f"{n:2}    {r['packs']:2}    {r['capacity']:2}")
    print()
    print("marginal guests per added pack (PACK=8):", marginal, "-> no zero-return pack")
    print("the author's pack=3 example, capacity(k):", thin, "-> first added pack returns nothing")
    print("thresholds where the purchase grows:", [n for n in range(2, MAX_GUESTS + 1) if row(n)["is_threshold"]])

    if bad:
        print("\nFAILED:")
        for b in bad:
            print("  " + b)
        return 1
    print(f"\nOK: {len(PUBLISHED)} published expectations reproduced, invariants hold for N=1..{MAX_GUESTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
