import math


def kelly_fraction(win_prob: float, win_ratio: float) -> float:
    if win_prob <= 0 or win_prob >= 1:
        return 0
    q = 1 - win_prob
    return max(0, (win_prob * win_ratio - q) / win_ratio)


def fixed_fraction(capital: float, fraction: float = 0.02) -> float:
    return capital * fraction
