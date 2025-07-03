from my_db.enums import CombinationStatus


def has_cut_combination(combinations):
    for combo in combinations:
        if combo.get('status') == CombinationStatus.CUT:
            return True
    return False