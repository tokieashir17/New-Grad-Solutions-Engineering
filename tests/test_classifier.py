import unittest

from src.classifier import classify


class ClassifierTests(unittest.TestCase):
    def test_new_grad_solutions_engineer(self):
        result = classify(
            "Solutions Engineer",
            "We are hiring a new grad with 0-2 years of experience.",
            "New York, NY",
        )
        self.assertTrue(result["relevant"])
        self.assertTrue(result["early_career"])
        self.assertEqual(result["category"], "Solutions Engineering")

    def test_senior_is_excluded(self):
        result = classify(
            "Senior Solutions Engineer",
            "Build customer solutions.",
            "New York, NY",
        )
        self.assertFalse(result["relevant"])

    def test_fde(self):
        result = classify(
            "Forward Deployed Engineer",
            "Early-career engineers work directly with customers.",
            "Remote - United States",
        )
        self.assertTrue(result["relevant"])
        self.assertEqual(result["category"], "Forward Deployed Engineering")
        self.assertTrue(result["remote"])


if __name__ == "__main__":
    unittest.main()
