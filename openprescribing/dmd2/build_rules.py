def build_rules(search):
    """Return structure used to populate a QueryBuilder instance.

    `search` is a tree describing the search to be performed

    See https://querybuilder.js.org/#method-setRules for expected structure of rules.

    See TestAdvancedSearchHelpers.test_build_rules for an example.
    """

    rules = _build_rules_helper(search)
    if "condition" not in rules:
        rules = {"condition": "AND", "rules": [rules]}
    return rules


def _build_rules_helper(search):
    """Helper function for build_rules().

    A branch node like:

        ["and", [node1, node2]]

    will be transformed, recursively, into:

        {
            "condition": "AND",
            "rules": [_build_rules_helper(node1), _build_rules_helper(node2)]
        }

    A leaf node like:

        ["nm", "contains", "paracetamol"]

    will be transformed into:

        {"id": "nm", "operator": "contains", "value": "paracetamol"}
    """

    assert len(search) in [2, 3]

    if len(search) == 2:
        # branch node
        return {
            "condition": search[0].upper(),
            "rules": map(_build_rules_helper, search[1]),
        }
    else:
        # leaf node
        value = search[2]
        if value is True:
            value = 1
        elif value is False:
            value = 0

        return {"id": search[0], "operator": search[1], "value": value}
