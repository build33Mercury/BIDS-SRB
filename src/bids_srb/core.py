from __future__ import annotations
from pathlib import Path, PurePosixPath
import copy, hashlib, json, re
from .errors import ManifestError, UnsafePathError, ComputeLockedError

# Canonicalization is exact-path scoped. A field is never removed merely because
# its key *looks* volatile.
VOLATILE_EXACT_PATHS = {
    ("environment","free_mem"): "<VOLATILE_FREE_MEM_AT_START>",
    ("execution","run_uuid"): "<VOLATILE_RUN_UUID>",
    ("execution","run_id"): "<VOLATILE_RUN_ID>",
    ("runtime","timestamp"): "<VOLATILE_TIMESTAMP>",
    ("runtime","started_at"): "<VOLATILE_TIMESTAMP>",
    ("runtime","ended_at"): "<VOLATILE_TIMESTAMP>",
    ("runtime","transient_cache_root"): "<VOLATILE_CACHE_ROOT>",
}
UNORDERED_LIST_PATHS = {("runtime","completed_workers")}
WORK_PATH_KEYS = {("execution","work_dir"),("execution","work_dir_base"),("runtime","work_root")}
COMPOSITE_RUN_ID = re.compile(
    r"(?i)(?<![0-9a-f])20\d{6}-[0-2]\d[0-5]\d[0-5]\d_"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
    r"(?![0-9a-f])"
)

CASE_MANIFEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "BIDS-SRB Case Manifest",
    "type": "object",
    "required": ["case_id","fixture_class","operator","files"],
    "properties": {
        "case_id": {"type":"string","minLength":1},
        "fixture_class": {"enum":["synthetic","external_static","empirical"]},
        "operator": {"type":"string","minLength":1},
        "files": {
            "type":"array",
            "items": {
                "type":"object",
                "required":["path"],
                "properties":{
                    "path":{"type":"string","minLength":1},
                    "sha256":{"type":"string","pattern":"^[0-9a-fA-F]{64}$"},
                    "json":{"type":"object"},
                    "text":{"type":"string"},
                },
                "additionalProperties": True,
            },
        },
        "expected":{"type":"object"},
        "mutation":{"type":"object"},
        "repair":{"type":"object"},
    },
    "additionalProperties": True,
}

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_relative_path(value: str) -> Path:
    if not isinstance(value,str) or not value or "\\" in value:
        raise UnsafePathError(f"Unsafe relative path: {value!r}")
    # Check raw path components before PurePosixPath normalizes "." away.
    raw_parts=value.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        raise UnsafePathError(f"Unsafe relative path: {value!r}")
    p=PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts:
        raise UnsafePathError(f"Unsafe relative path: {value!r}")
    return Path(*p.parts)

def _inside(root: Path, child: Path) -> bool:
    root=root.resolve()
    child=child.resolve()
    return child == root or root in child.parents

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def schema_document() -> dict:
    return copy.deepcopy(CASE_MANIFEST_SCHEMA)

def _validate_schema_shape(schema: dict) -> None:
    if not isinstance(schema,dict) or schema.get("type")!="object":
        raise ManifestError("Case schema root must be an object schema")
    if schema.get("required") != ["case_id","fixture_class","operator","files"]:
        raise ManifestError("Case schema required-field contract drifted")
    props=schema.get("properties")
    if not isinstance(props,dict):
        raise ManifestError("Case schema properties missing")
    if set(["case_id","fixture_class","operator","files"]) - set(props):
        raise ManifestError("Case schema missing required property definitions")

def validate_manifest(data: dict) -> dict:
    _validate_schema_shape(CASE_MANIFEST_SCHEMA)
    if not isinstance(data,dict):
        raise ManifestError("Manifest must be an object")
    for key in CASE_MANIFEST_SCHEMA["required"]:
        if key not in data:
            raise ManifestError(f"Missing required key: {key}")
    if not isinstance(data["case_id"],str) or not data["case_id"].strip():
        raise ManifestError("case_id must be a non-empty string")
    if data["fixture_class"] not in {"synthetic","external_static","empirical"}:
        raise ManifestError("Invalid fixture_class")
    if not isinstance(data["operator"],str) or not data["operator"].strip():
        raise ManifestError("operator must be a non-empty string")
    if not isinstance(data["files"],list):
        raise ManifestError("files must be a list")
    seen=set()
    for i,rec in enumerate(data["files"]):
        if not isinstance(rec,dict) or "path" not in rec:
            raise ManifestError(f"File record {i} needs path")
        rel=safe_relative_path(rec["path"]).as_posix()
        if rel in seen:
            raise ManifestError(f"Duplicate path: {rel}")
        seen.add(rel)
        if "sha256" in rec:
            s=rec["sha256"]
            if not isinstance(s,str) or re.fullmatch(r"[0-9a-fA-F]{64}",s) is None:
                raise ManifestError(f"Invalid sha256 for {rel}")
        if "json" in rec and not isinstance(rec["json"],dict):
            raise ManifestError(f"json payload must be an object for {rel}")
        if "text" in rec and not isinstance(rec["text"],str):
            raise ManifestError(f"text payload must be a string for {rel}")
        if "json" in rec and "text" in rec:
            raise ManifestError(f"File record must not contain both json and text: {rel}")
    return {
        "valid":True,
        "case_id":data["case_id"],
        "fixture_class":data["fixture_class"],
        "file_count":len(data["files"]),
        "schema_title":CASE_MANIFEST_SCHEMA["title"],
    }

def inspect_dataset(root: Path) -> dict:
    root=root.resolve()
    if not root.is_dir():
        raise ManifestError(f"Dataset directory not found: {root}")
    desc=root/"dataset_description.json"
    meta={}
    if desc.exists():
        try: meta=load_json(desc)
        except Exception as e: raise ManifestError(f"Invalid dataset_description.json: {e}") from e
    files=[p for p in root.rglob("*") if p.is_file()]
    return {
        "dataset":root.name,
        "BIDSVersion":meta.get("BIDSVersion"),
        "file_count":len(files),
        "extensions":dict(sorted(_count_ext(files).items())),
        "read_only":True,
    }

def _count_ext(files):
    out={}
    for p in files:
        name=p.name
        ext=".nii.gz" if name.endswith(".nii.gz") else p.suffix.lower() or "<none>"
        out[ext]=out.get(ext,0)+1
    return out

def make_plan(manifest: dict) -> dict:
    v=validate_manifest(manifest)
    return {
        "case_id":v["case_id"],
        "fixture_class":v["fixture_class"],
        "operator":manifest["operator"],
        "steps":[
            "validate_manifest","verify_baseline","apply_operator",
            "verify_payload","adapter_stage_LOCKED","repair_stage_if_synthetic"
        ],
        "scientific_execution_authorized":False,
    }

def generate_synthetic(manifest: dict, out: Path) -> dict:
    validate_manifest(manifest)
    if manifest["fixture_class"]!="synthetic":
        raise ComputeLockedError("generate is limited to synthetic fixtures in this candidate")
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    written=[]
    for rec in manifest["files"]:
        rel=safe_relative_path(rec["path"])
        target=(out/rel).resolve()
        if not _inside(out,target):
            raise UnsafePathError(str(rel))
        target.parent.mkdir(parents=True,exist_ok=True)
        if "json" in rec:
            target.write_text(json.dumps(rec["json"],indent=2,sort_keys=True)+"\n",encoding="utf-8")
        else:
            target.write_text(rec.get("text",""),encoding="utf-8")
        written.append({"path":rel.as_posix(),"sha256":sha256_file(target)})
    return {"case_id":manifest["case_id"],"written":written,"synthetic_only":True}

def verify_files(manifest: dict, root: Path) -> dict:
    validate_manifest(manifest)
    root=root.resolve()
    rows=[]
    ok=True
    for rec in manifest["files"]:
        rel=safe_relative_path(rec["path"])
        p=(root/rel).resolve()
        if not _inside(root,p):
            raise UnsafePathError(str(rel))
        exists=p.exists() and p.is_file()
        observed=sha256_file(p) if exists else None
        expected=rec.get("sha256")
        match=exists and (expected is None or observed.lower()==expected.lower())
        ok = bool(ok and match)
        rows.append({
            "path":rel.as_posix(),"exists":exists,
            "expected_sha256":expected,"observed_sha256":observed,"match":match
        })
    return {"valid":bool(ok),"files":rows}

def _norm_work_path(s: str) -> str:
    x=s.replace("\\","/")
    x=COMPOSITE_RUN_ID.sub("<RUNID>",x)
    m=re.search(r"(?i)(?:^|/)(work|workdir)(/.*)?$",x)
    if m:
        return "<WORKROOT>/"+m.group(1).lower()+(m.group(2) or "")
    return x

def canonicalize(obj, path=()):
    if path in VOLATILE_EXACT_PATHS:
        return VOLATILE_EXACT_PATHS[path]
    if isinstance(obj,dict):
        return {
            str(k):canonicalize(v,path+(str(k),))
            for k,v in sorted(obj.items(),key=lambda kv:str(kv[0]))
        }
    if isinstance(obj,list):
        vals=[canonicalize(v,path+("[]",)) for v in obj]
        if path in UNORDERED_LIST_PATHS:
            return sorted(vals,key=lambda x:json.dumps(x,sort_keys=True,separators=(",",":")))
        return vals
    if isinstance(obj,tuple):
        return canonicalize(list(obj),path)
    if isinstance(obj,str) and path in WORK_PATH_KEYS:
        return _norm_work_path(obj)
    return obj

def compare(a,b):
    ca,cb=canonicalize(a),canonicalize(b)
    return {"equal":ca==cb,"left":ca,"right":cb}

def apply_synthetic_mutation(manifest: dict, root: Path) -> dict:
    validate_manifest(manifest)
    if manifest.get("fixture_class")!="synthetic":
        raise ComputeLockedError("Mutation is synthetic-only")
    mut=manifest.get("mutation") or {}
    if "path" not in mut:
        raise ManifestError("mutation.path missing")
    rel=safe_relative_path(mut["path"])
    root=root.resolve()
    p=(root/rel).resolve()
    if not _inside(root,p):
        raise UnsafePathError(str(rel))
    data=load_json(p)
    key=mut.get("remove_key")
    if key:
        data.pop(key,None)
    p.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return {"path":rel.as_posix(),"sha256":sha256_file(p)}

def repair_synthetic(manifest: dict, root: Path) -> dict:
    validate_manifest(manifest)
    if manifest.get("fixture_class")!="synthetic":
        raise ComputeLockedError("Repair is synthetic-only in this candidate")
    rep=manifest.get("repair") or {}
    if "path" not in rep:
        raise ManifestError("repair.path missing")
    rel=safe_relative_path(rep["path"])
    root=root.resolve()
    p=(root/rel).resolve()
    if not _inside(root,p):
        raise UnsafePathError(str(rel))
    data=load_json(p)
    for k,v in (rep.get("set") or {}).items():
        data[k]=v
    p.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return {"path":rel.as_posix(),"sha256":sha256_file(p),"repair_applied":True}

def execute_locked(*args,**kwargs):
    raise ComputeLockedError(
        "BIDS-SRB scientific execution is locked in 0.1.0.dev1; "
        "Gate 20 software work does not grant COMPUTE-GO"
    )

def make_report(record: dict) -> dict:
    return {
        "project":"BIDS-SRB",
        "record":canonicalize(record),
        "scientific_execution_authorized":False,
        "claim_ceiling":"diagnostic software evidence only",
    }

def provenance(action: str, inputs: dict, outputs: dict) -> dict:
    return {
        "@context":"https://www.w3.org/ns/prov.jsonld",
        "type":"BIDS-SRB SoftwareEvidence",
        "action":action,
        "inputs":canonicalize(inputs),
        "outputs":canonicalize(outputs),
        "scientific_execution_authorized":False,
    }
