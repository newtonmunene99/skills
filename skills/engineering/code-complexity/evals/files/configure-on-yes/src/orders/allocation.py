def allocate_stock(order: dict, warehouses: list[dict], *, allow_split: bool = False) -> list[dict]:
    """Pick warehouse lines that fulfil the order, preferring a single warehouse."""
    picks: list[dict] = []
    for line in order["lines"]:
        needed = line["qty"]
        for warehouse in warehouses:
            if warehouse["region"] == order["region"] or allow_split:
                if warehouse.get("active", True):
                    for bin_ in warehouse["bins"]:
                        if bin_["sku"] == line["sku"] and bin_["qty"] > 0:
                            take = min(needed, bin_["qty"])
                            if take < needed and not allow_split:
                                continue
                            picks.append(
                                {"warehouse": warehouse["id"], "sku": line["sku"], "qty": take}
                            )
                            needed -= take
                            if needed == 0:
                                break
            if needed == 0:
                break
        if needed:
            raise LookupError(f"cannot allocate {line['sku']}")
    return picks


def total_weight(order: dict, weights: dict[str, int]) -> int:
    return sum(weights[line["sku"]] * line["qty"] for line in order["lines"])
