from pathlib import Path
import json, tempfile, unittest
from bids_srb.core import canonicalize, load_json, validate_manifest, provenance
ROOT=Path(__file__).parents[1]

class MaturityTests(unittest.TestCase):
    def test_golden_canonicalizer(self):
        inp=load_json(ROOT/"fixtures/golden/canonical_input.json")
        expected=load_json(ROOT/"fixtures/golden/canonical_expected_v3.json")
        self.assertEqual(canonicalize(inp),expected)

    def test_provenance_is_science_locked(self):
        p=provenance("static_test",{"runtime":{"timestamp":"x"}},{"ok":True})
        self.assertFalse(p["scientific_execution_authorized"])
        self.assertEqual(p["inputs"]["runtime"]["timestamp"],"<VOLATILE_TIMESTAMP>")

if __name__=="__main__": unittest.main()
