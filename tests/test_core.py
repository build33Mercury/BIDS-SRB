from pathlib import Path
import json, tempfile, unittest
from bids_srb.core import *
from bids_srb.errors import *

ROOT=Path(__file__).parents[1]

class CoreTests(unittest.TestCase):
    def test_unsafe_paths_fail_closed(self):
        for p in ("../x","/tmp/x","a/../../b","a\\b",".",""):
            with self.assertRaises(UnsafePathError): safe_relative_path(p)

    def test_manifest_validation_and_schema_contract(self):
        m={"case_id":"x","fixture_class":"synthetic","operator":"demo","files":[{"path":"a.json","json":{}}]}
        self.assertTrue(validate_manifest(m)["valid"])
        disk=load_json(ROOT/"schemas/case-manifest.schema.json")
        self.assertEqual(disk, schema_document())

    def test_manifest_rejects_bad_types_and_dupes(self):
        bads=[
          {"case_id":"","fixture_class":"synthetic","operator":"x","files":[]},
          {"case_id":"x","fixture_class":"bad","operator":"x","files":[]},
          {"case_id":"x","fixture_class":"synthetic","operator":"","files":[]},
          {"case_id":"x","fixture_class":"synthetic","operator":"x","files":[{"path":"a"},{"path":"a"}]},
          {"case_id":"x","fixture_class":"synthetic","operator":"x","files":[{"path":"a","sha256":"xyz"}]},
          {"case_id":"x","fixture_class":"synthetic","operator":"x","files":[{"path":"a","json":{},"text":"x"}]},
        ]
        for m in bads:
            with self.assertRaises(ManifestError): validate_manifest(m)

    def test_execute_is_hard_locked(self):
        with self.assertRaises(ComputeLockedError): execute_locked({})

    def test_canonicalization_exact_path_only(self):
        a={
          "timestamp":"SEMANTIC_TOP_LEVEL",
          "environment":{"free_mem":5.8},
          "execution":{"run_uuid":"11111111-1111-4111-8111-111111111111","work_dir":"C:/x/work/20260905-064257_11111111-1111-4111-8111-111111111111/app"},
          "workflow":{"semantic_uuid":"550e8400-e29b-41d4-a716-446655440000","ordered":["A","B"]}
        }
        b=json.loads(json.dumps(a))
        b["environment"]["free_mem"]=5.1
        b["execution"]["run_uuid"]="22222222-2222-4222-8222-222222222222"
        b["execution"]["work_dir"]="D:/y/work/20260905-064350_22222222-2222-4222-8222-222222222222/app"
        self.assertEqual(canonicalize(a),canonicalize(b))
        c=json.loads(json.dumps(b)); c["timestamp"]="DIFFERENT_SEMANTIC_TOP_LEVEL"
        self.assertNotEqual(canonicalize(a),canonicalize(c))
        d=json.loads(json.dumps(b)); d["workflow"]["semantic_uuid"]="650e8400-e29b-41d4-a716-446655440000"
        self.assertNotEqual(canonicalize(a),canonicalize(d))
        e=json.loads(json.dumps(b)); e["workflow"]["ordered"]=["B","A"]
        self.assertNotEqual(canonicalize(a),canonicalize(e))

    def test_synthetic_apply_repair_identity(self):
        m={"case_id":"s","fixture_class":"synthetic","operator":"json_remove_key",
           "files":[{"path":"x.json","json":{"RepetitionTime":2,"TaskName":"x"}}],
           "mutation":{"path":"x.json","remove_key":"RepetitionTime"},
           "repair":{"path":"x.json","set":{"RepetitionTime":2}}}
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); generate_synthetic(m,r); before=(r/"x.json").read_bytes()
            apply_synthetic_mutation(m,r); self.assertNotEqual(before,(r/"x.json").read_bytes())
            repair_synthetic(m,r); self.assertEqual(json.loads(before),json.loads((r/"x.json").read_bytes()))

    def test_empirical_mutation_and_repair_refused(self):
        m={"case_id":"e","fixture_class":"empirical","operator":"x","files":[],"mutation":{"path":"x.json","remove_key":"x"},"repair":{"path":"x.json","set":{"x":1}}}
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ComputeLockedError): apply_synthetic_mutation(m,Path(td))
            with self.assertRaises(ComputeLockedError): repair_synthetic(m,Path(td))

    def test_report_lock(self):
        rep=make_report({"runtime":{"timestamp":"now"},"result":"static"})
        self.assertFalse(rep["scientific_execution_authorized"])
        self.assertEqual(rep["record"]["runtime"]["timestamp"],"<VOLATILE_TIMESTAMP>")

    def test_property_like_repair_identity_across_values(self):
        for value in [0,0.5,1,2,3.14159,9.9]:
            m={"case_id":f"s{value}","fixture_class":"synthetic","operator":"json_remove_key",
               "files":[{"path":"x.json","json":{"RepetitionTime":value,"TaskName":"x"}}],
               "mutation":{"path":"x.json","remove_key":"RepetitionTime"},
               "repair":{"path":"x.json","set":{"RepetitionTime":value}}}
            with tempfile.TemporaryDirectory() as td:
                r=Path(td); generate_synthetic(m,r); before=sha256_file(r/"x.json")
                apply_synthetic_mutation(m,r); repair_synthetic(m,r)
                self.assertEqual(before,sha256_file(r/"x.json"))

if __name__=="__main__": unittest.main()
