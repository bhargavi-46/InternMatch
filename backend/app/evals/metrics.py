import math


def precision_at_k(gains: list[int], k: int) -> float:
    return sum(1 for g in gains[:k] if g > 0) / k


def ndcg_at_k(gains: list[int], ideal_gains: list[int], k: int) -> float:
    def dcg(values: list[int]) -> float:
        return sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(values[:k]))

    ideal = dcg(sorted(ideal_gains, reverse=True))
    return dcg(gains) / ideal if ideal else 0.0


def reciprocal_rank(gains: list[int]) -> float:
    for i, g in enumerate(gains):
        if g > 0:
            return 1.0 / (i + 1)
    return 0.0
