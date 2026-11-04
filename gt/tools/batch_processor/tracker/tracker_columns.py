"""Pure helpers for keeping table column proportions stable while a window is resized."""


def capture_column_ratios(widths):
    """Converts column widths into fractions of their total.

    Args:
        widths (list): Current column widths in pixels.

    Returns:
        list: Fractions that sum to 1, or an empty list when there is nothing to measure.
    """
    total_width = float(sum(widths))
    if total_width <= 0:
        return []
    return [width / total_width for width in widths]


def distribute_column_widths(ratios, total_width, minimum_width):
    """Splits a width between columns by ratio without any cumulative drift.

    Columns that would fall under the minimum are pinned to it and the rest share
    what is left. Rounding uses the largest-remainder method so the integer widths
    add up to the requested total (or to the sum of the minimums when that is larger).

    Args:
        ratios (list): Column fractions from ``capture_column_ratios``.
        total_width (int): Available width in pixels.
        minimum_width (int): Smallest allowed column width in pixels.

    Returns:
        list: Integer width for each column.
    """
    count = len(ratios)
    if not count:
        return []
    pinned = set()
    widths = [0.0] * count
    while True:
        free_indexes = [index for index in range(count) if index not in pinned]
        free_total = total_width - minimum_width * len(pinned)
        free_ratio = sum(ratios[index] for index in free_indexes)
        newly_pinned = False
        for index in free_indexes:
            share = ratios[index] / free_ratio if free_ratio > 0 else 1.0 / len(free_indexes)
            widths[index] = share * free_total
            if widths[index] < minimum_width:
                pinned.add(index)
                newly_pinned = True
        if not newly_pinned or len(pinned) == count:
            break
    for index in pinned:
        widths[index] = float(minimum_width)
    target_total = max(int(round(total_width)), int(minimum_width * count))
    result = [int(width) for width in widths]
    shortfall = target_total - sum(result)
    if shortfall > 0:
        order = sorted(
            (index for index in range(count) if index not in pinned),
            key=lambda index: widths[index] - result[index],
            reverse=True,
        ) or list(range(count))
        for position in range(shortfall):
            result[order[position % len(order)]] += 1
    return result
