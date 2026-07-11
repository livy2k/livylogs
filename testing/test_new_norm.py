import unittest
from utils import normalize_name

class TestNormalization(unittest.TestCase):
    def test_npc_articles(self):
        self.assertEqual(normalize_name("a Krayt Drag Unknown"), "Krayt Drag")
        self.assertEqual(normalize_name("an Imperial S trooper"), "Imperial S trooper")
        self.assertEqual(normalize_name("the Rancor"), "Rancor")
        self.assertEqual(normalize_name("a Rebel Col Unknown"), "Rebel Col")
        self.assertEqual(normalize_name("Rebel Major General"), "Rebel Major General")

    def test_parentheses(self):
        self.assertEqual(normalize_name("Livy (Melee)"), "Livy")
        self.assertEqual(normalize_name("Stormtrooper (Ranged)"), "Stormtrooper")
        self.assertEqual(normalize_name("Some Name (Extra Info) with more"), "Some Name  with more")

    def test_nested_complex(self):
        # Case from user: "th Shot II a Krayt Drag Unknown"
        self.assertEqual(normalize_name("th Shot II a Krayt Drag Unknown"), "Krayt Drag")
        self.assertEqual(normalize_name("a Krayt Drag (Something) Unknown"), "Krayt Drag")

    def test_strip_repeated(self):
        self.assertEqual(normalize_name("a a an the Name unknown unknown"), "Name")

if __name__ == "__main__":
    unittest.main()
