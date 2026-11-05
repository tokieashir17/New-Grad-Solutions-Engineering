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

    def test_customer_success_engineer(self):
        result = classify(
            "Customer Success Engineer",
            "Entry-level role helping customers adopt the platform.",
            "New York, NY",
        )
        self.assertTrue(result["relevant"])
        self.assertEqual(result["category"], "Customer Success Engineering")
        self.assertTrue(result["early_career"])

    def test_developer_advocate(self):
        result = classify(
            "Developer Advocate",
            "New grad opportunity building demos and talking to developers.",
            "San Francisco, CA",
        )
        self.assertTrue(result["relevant"])
        self.assertEqual(result["category"], "Developer Advocacy")

    def test_technical_support_engineer(self):
        result = classify(
            "Technical Support Engineer",
            "Associate role troubleshooting customer issues.",
            "Boston, MA",
        )
        self.assertTrue(result["relevant"])
        self.assertEqual(result["category"], "Technical Support Engineering")

    def test_partner_engineer(self):
        result = classify(
            "Partner Engineer",
            "Early-career engineers enabling partner integrations.",
            "Remote - United States",
        )
        self.assertTrue(result["relevant"])
        self.assertEqual(result["category"], "Partner Engineering")

    def test_bdr_title_excluded(self):
        result = classify(
            "BDR - Enterprise",
            "Work with solutions engineers on deals.",
            "New York, NY",
        )
        self.assertFalse(result["relevant"])


if __name__ == "__main__":
    unittest.main()
