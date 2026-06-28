"""A compact, dependency-free Glicko-2 implementation.

Glicko-2 (Glickman, 2013 - http://www.glicko.net/glicko/glicko2.pdf) tracks for
each competitor a rating, a rating deviation (RD, the uncertainty of the
rating) and a volatility.  Compared with Elo it (a) reports how *confident* we
are in each rating and (b) updates faster when results are surprising -- both
properties we exploit to pick informative match-ups for a noisy, crowd-sourced
"who would win" tier list.

Ratings are stored on the familiar Glicko scale (mean 1500).  Internally the
update works on the Glicko-2 scale (mu, phi); the 173.7178 factor converts
between them.
"""
import math

SCALE = 173.7178
DEFAULT_RATING = 1500.0
DEFAULT_RD = 350.0
DEFAULT_VOL = 0.06
TAU = 0.5          # constrains volatility change; smaller = steadier
EPSILON = 1e-6


class Rating:
    __slots__ = ("rating", "rd", "vol")

    def __init__(self, rating=DEFAULT_RATING, rd=DEFAULT_RD, vol=DEFAULT_VOL):
        self.rating = rating
        self.rd = rd
        self.vol = vol

    # --- scale conversions -------------------------------------------------
    @property
    def mu(self):
        return (self.rating - DEFAULT_RATING) / SCALE

    @property
    def phi(self):
        return self.rd / SCALE

    def as_dict(self):
        return {"rating": self.rating, "rd": self.rd, "vol": self.vol}


def _g(phi):
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi * math.pi))


def expected_score(player, opponent):
    """Probability that ``player`` beats ``opponent`` (Glicko-2)."""
    return 1.0 / (1.0 + math.exp(-_g(opponent.phi) * (player.mu - opponent.mu)))


def rate(player, results, tau=TAU):
    """Return an updated :class:`Rating` for ``player``.

    ``results`` is a list of ``(opponent_rating, score)`` where score is 1.0
    for a win, 0.0 for a loss, 0.5 for a draw.  If empty, only the deviation
    grows (the rating becomes less certain over time / inactivity).
    """
    if not results:
        phi_star = math.sqrt(player.phi ** 2 + player.vol ** 2)
        return Rating(player.rating, min(phi_star * SCALE, DEFAULT_RD), player.vol)

    mu = player.mu
    v_inv = 0.0
    delta_sum = 0.0
    for opp, score in results:
        g = _g(opp.phi)
        e = 1.0 / (1.0 + math.exp(-g * (mu - opp.mu)))
        v_inv += g * g * e * (1.0 - e)
        delta_sum += g * (score - e)
    v = 1.0 / v_inv
    delta = v * delta_sum

    # Iteratively solve for the new volatility (Illinois algorithm).
    a = math.log(player.vol ** 2)
    phi2 = player.phi ** 2

    def f(x):
        ex = math.exp(x)
        num = ex * (delta * delta - phi2 - v - ex)
        den = 2.0 * (phi2 + v + ex) ** 2
        return num / den - (x - a) / (tau * tau)

    A = a
    if delta * delta > phi2 + v:
        B = math.log(delta * delta - phi2 - v)
    else:
        k = 1
        while f(a - k * tau) < 0:
            k += 1
        B = a - k * tau

    fa, fb = f(A), f(B)
    while abs(B - A) > EPSILON:
        C = A + (A - B) * fa / (fb - fa)
        fc = f(C)
        if fc * fb <= 0:
            A, fa = B, fb
        else:
            fa /= 2.0
        B, fb = C, fc

    new_vol = math.exp(A / 2.0)
    phi_star = math.sqrt(phi2 + new_vol ** 2)
    new_phi = 1.0 / math.sqrt(1.0 / (phi_star ** 2) + 1.0 / v)
    new_mu = mu + new_phi ** 2 * delta_sum

    return Rating(
        rating=new_mu * SCALE + DEFAULT_RATING,
        rd=new_phi * SCALE,
        vol=new_vol,
    )
