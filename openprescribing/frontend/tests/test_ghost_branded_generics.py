from django.test import TestCase
from frontend import ghost_branded_generics as gbg


class TestPresentationsToIgnore(TestCase):
    def test_missing_commas(self):
        for presentation in gbg.PRESENTATIONS_TO_IGNORE:
            self.assertGreater(
                len(presentation),
                1,
                f"'{presentation}' does not look like a BNF code, "
                f"are you missing square brackets around the list?",
            )
            self.assertLessEqual(
                len(presentation),
                15,
                f"'{presentation}' does not look like a BNF code, "
                f"are you missing commas?",
            )
