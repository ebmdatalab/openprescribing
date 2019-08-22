def build_rules(search):
    """Return structure used to populate a QueryBuilder instance.

    See https://querybuilder.js.org/#method-setRules
    """

    rules = _build_rules_helper(search)
    if "condition" not in rules:
        rules = {"condition": "AND", "rules": [rules]}
    return rules


def _build_rules_helper(search):
    assert len(search) in [2, 3]

    if len(search) == 2:
        return {
            "condition": search[0].upper(),
            "rules": map(_build_rules_helper, search[1]),
        }
    else:
        value = search[2]
        if value is True:
            value = 1
        elif value is False:
            value = 0

        return {"id": search[0], "operator": search[1], "value": value}
