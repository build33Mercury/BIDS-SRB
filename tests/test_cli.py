from pathlib import Path
import json, subprocess, sys, tempfile, unittest, os

class CliTests(unittest.TestCase):
    def run_cli(self,*args):
        env=dict(os.environ); env["PYTHONPATH"]=str(Path(__file__).parents[1]/"src")
        return subprocess.run([sys.executable,"-m","bids_srb.cli",*args],env=env,text=True,capture_output=True)

    def test_execute_cli_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; p.write_text(json.dumps({"case_id":"x","fixture_class":"synthetic","operator":"x","files":[]}))
            r=self.run_cli("execute",str(p))
            self.assertEqual(r.returncode,2)
            data=json.loads(r.stdout)
            self.assertEqual(data["status"],"FAIL_CLOSED")
            self.assertFalse(data["scientific_execution_authorized"])

    def test_version_and_schema_are_structured(self):
        r=self.run_cli("version"); self.assertEqual(r.returncode,0); self.assertEqual(json.loads(r.stdout)["version"],"0.1.0.dev1")
        r=self.run_cli("schema"); self.assertEqual(r.returncode,0); self.assertEqual(json.loads(r.stdout)["title"],"BIDS-SRB Case Manifest")

    def test_plan_is_static(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; p.write_text(json.dumps({"case_id":"x","fixture_class":"synthetic","operator":"x","files":[]}))
            r=self.run_cli("plan",str(p)); self.assertEqual(r.returncode,0); self.assertFalse(json.loads(r.stdout)["scientific_execution_authorized"])

if __name__=="__main__": unittest.main()
