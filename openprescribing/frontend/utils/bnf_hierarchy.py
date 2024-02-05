from matrixstore.db import get_db


def simplify_bnf_codes(bnf_codes):
    """Given list of BNF codes, return list of BNF prefixes for BNF subsections such
    that:

        1. every BNF code that belongs to one of these prefixes is in the original list,
        2. every code in the original list belongs to exactly one prefix,
        3. no prefix is a prefix of another prefix (I think this follows from 2),
        4. every prefix is present in the prescribing data.

    A BNF prefix may actually be a full BNF code.
    """

    all_bnf_codes = get_all_bnf_codes()

    # Drop any BNF codes for which we don't have prescribing.
    bnf_codes_with_prescribing = set(bnf_codes) & all_bnf_codes

    # In end-to-end tests there may be no prescribing for certain measures.  Rather than
    # adding new test prescribing data whenever a new measure is added, we return early
    # here.
    if not bnf_codes_with_prescribing:
        return sorted(bnf_codes)

    prefixes = []

    for prefix in _prune_paths(bnf_codes_with_prescribing, all_bnf_codes):
        prefixes.extend(get_subsection_prefixes(prefix))

    return sorted(prefixes)


def get_all_bnf_codes():
    """Return list of all BNF codes for which we have prescribing."""

    db = get_db()
    return {r[0] for r in db.query("SELECT bnf_code FROM presentation")}


def get_subsection_prefixes(prefix):
    """Return BNF codes/prefixes of BNF subsections that begin with `prefix`.

    For instance, if `prefix` is "0703021", we find all prefixes corresponding to
    chemicals beginning 0703021.
    """

    for length in [
        2,  # Chapter
        4,  # Section
        6,  # Paragraph
        7,  # Subparagraph
        9,  # Chemical
        11,  # Product
        15,  # Presentation
    ]:
        if len(prefix) <= length:
            break

    db = get_db()
    sql = (
        "SELECT DISTINCT substr(bnf_code, 1, ?) FROM presentation WHERE bnf_code LIKE ?"
    )
    return {r[0] for r in db.query(sql, [length, prefix + "%"])}


def _prune_paths(paths, all_paths):
    r"""Given two lists of paths (`paths` and `all_paths`) from the root of a tree to its
    leaves (where every path in `paths` is in `all_paths`) return a new list of
    paths from the root of the tree to either a leaf or a branch (`pruned_paths`) such
    that:

        1. every path in `all_paths` that is reachable from a path in `pruned_paths` is
            in `paths`,
        2. every path in `paths` is reachable from exactly one path in `pruned_paths`,
        3. no path in `pruned_paths` is reachable from another path in `pruned_paths`.

    These three conditions correspond to those in the docstring for simplify_bnf_codes.

    For instance:

        all_paths: [AAA, AAB, ABA, ABB, BAA, BAB, BBA, BBB]
        paths:     [AAA,      ABA, ABB, BAA, BAB,         ]

    To do this, we convert `paths` and `all_paths` into trees:

        all_paths:                  paths:

                   A                           A
                  /                           /
                 A                           A
                / \                         /
               /   B                       /
              A                           A
             / \   A                     / \   A
            /   \ /                     /   \ /
           /     B                     /     B
          /       \                   /       \
         /         B                 /         B
        o                           o
         \         A                 \         A
          \       /                   \       /
           \     A                     \     A
            \   / \                     \   / \
             \ /   B                     \ /   B
              B                           B
               \   A
                \ /
                 B
                  \
                   B

    We then prune the `paths` tree, where for each node, we remove all of the node's
    children if all of the children are in the `all_paths` tree.

    So we remove the children of AB (since ABA and ABB are in `paths`) and BA (since BAA
    and BAB are in `paths`).

    This leaves:

                   A
                  /
                 A
                /
               /
              A
             / \
            /   \
           /     B
          /
         /
        o
         \
          \
           \     A
            \   /
             \ /
              B

    Finally, we walk this pruned tree to give:

    pruned_paths: [AAA, AB, BA]

    A tree is representated as a nested dictionary.  For instance, the `paths` tree is
    represented as:

    {
        "A": {
            "A": {
                "A": {},
            },
            "B": {
                "A": {},
                "B": {}
            }
        },
        "B": {
            "A": {
                "A": {},
                "B": {}
            }
        },
    }

    And the `pruned_paths` tree:

    {
        "A": {
            "A": {
                "A": {}
            },
            "B": {}
        },
        "B": {
            "A": {}
        }
    }

    There is a test case for this example at TestPrunePaths.test_example.
    """

    assert set(paths) < set(all_paths)  # `paths` must be a subset of `all_paths`

    full_tree = _paths_to_tree(all_paths)
    subtree = _paths_to_tree(paths)
    pruned_subtree = _prune_tree(subtree, full_tree)
    pruned_paths = _tree_to_paths(pruned_subtree)

    # We now verify the three conditions in the docstring hold.

    # 1. every path in `all_paths` that is reachable from a path in `pruned_paths` is in
    #     `paths`.
    for path in all_paths:
        if any(path.startswith(pruned_path) for pruned_path in pruned_paths):
            assert path in paths

    # 2. every path in `paths` is reachable from exactly one path in `pruned_paths`.
    for path in paths:
        # print(path)
        parent_pruned_paths = [
            pruned_path for pruned_path in pruned_paths if path.startswith(pruned_path)
        ]
        assert len(parent_pruned_paths) == 1

    # 3. no path in `pruned_paths` is reachable from another path in `pruned_paths`.
    for pruned_path_1 in pruned_paths:
        for pruned_path_2 in pruned_paths:
            if pruned_path_1 != pruned_path_2:
                assert not pruned_path_1.startswith(pruned_path_2)

    return pruned_paths


def _prune_tree(subtree, tree):
    """Do the work.

    I'm struggling to write a good docstring here.
    """

    if subtree == tree:
        return {}
    return {c: _prune_tree(subtree[c], tree[c]) for c in subtree}


def _paths_to_tree(paths):
    """Build a tree from the given paths.

    The structure of the tree is described in the docstring for _prune_paths.
    """

    tree = {}
    for path in paths:
        t = tree
        for c in path:
            if c not in t:
                t[c] = {}
            t = t[c]
    return tree


def _tree_to_paths(tree):
    """Build a list of paths made by walking from the root of the tree to each leaf."""

    if len(tree) == 0:
        return [""]
    return [
        c + path
        for c, subtree in sorted(tree.items())
        for path in _tree_to_paths(subtree)
    ]
