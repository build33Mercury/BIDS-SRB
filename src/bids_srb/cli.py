from __future__ import annotations
from pathlib import Path
import argparse, json
from . import __version__
from .core import (
    load_json, validate_manifest, inspect_dataset, make_plan, generate_synthetic,
    verify_files, execute_locked, canonicalize, compare, repair_synthetic,
    make_report, schema_document,
)
from .errors import BidsSrbError

def emit(obj):
    print(json.dumps(obj,indent=2,sort_keys=True))

def parser():
    p=argparse.ArgumentParser(prog="bids-srb")
    sp=p.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("version")
    a=sp.add_parser("schema")
    a=sp.add_parser("validate-manifest"); a.add_argument("manifest")
    a=sp.add_parser("inspect-dataset"); a.add_argument("dataset")
    a=sp.add_parser("plan"); a.add_argument("manifest")
    a=sp.add_parser("generate"); a.add_argument("manifest"); a.add_argument("--output-dir",required=True)
    a=sp.add_parser("verify"); a.add_argument("manifest"); a.add_argument("--root",required=True)
    a=sp.add_parser("execute"); a.add_argument("manifest")
    a=sp.add_parser("canonicalize"); a.add_argument("input"); a.add_argument("--output",required=True)
    a=sp.add_parser("compare"); a.add_argument("left"); a.add_argument("right")
    a=sp.add_parser("repair"); a.add_argument("manifest"); a.add_argument("--root",required=True)
    a=sp.add_parser("report"); a.add_argument("record"); a.add_argument("--output",required=True)
    a=sp.add_parser("replay"); a.add_argument("manifest"); a.add_argument("--output-dir",required=True)
    return p

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.cmd=="version": out={"project":"BIDS-SRB","version":__version__,"scientific_execution_authorized":False}
        elif args.cmd=="schema": out=schema_document()
        elif args.cmd=="validate-manifest": out=validate_manifest(load_json(Path(args.manifest)))
        elif args.cmd=="inspect-dataset": out=inspect_dataset(Path(args.dataset))
        elif args.cmd=="plan": out=make_plan(load_json(Path(args.manifest)))
        elif args.cmd=="generate": out=generate_synthetic(load_json(Path(args.manifest)),Path(args.output_dir))
        elif args.cmd=="verify": out=verify_files(load_json(Path(args.manifest)),Path(args.root))
        elif args.cmd=="execute": out=execute_locked(load_json(Path(args.manifest)))
        elif args.cmd=="canonicalize":
            out=canonicalize(load_json(Path(args.input)))
            Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        elif args.cmd=="compare": out=compare(load_json(Path(args.left)),load_json(Path(args.right)))
        elif args.cmd=="repair": out=repair_synthetic(load_json(Path(args.manifest)),Path(args.root))
        elif args.cmd=="report":
            out=make_report(load_json(Path(args.record)))
            Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        elif args.cmd=="replay":
            m=load_json(Path(args.manifest))
            gen=generate_synthetic(m,Path(args.output_dir))
            out={"replay":"STATIC_SYNTHETIC_RECONSTRUCTION_ONLY","generation":gen,"scientific_execution_authorized":False}
        emit(out)
        return 0
    except BidsSrbError as e:
        emit({"status":"FAIL_CLOSED","error_type":type(e).__name__,"error":str(e),"scientific_execution_authorized":False})
        return 2
    except Exception as e:
        emit({"status":"ERROR","error_type":type(e).__name__,"error":str(e),"scientific_execution_authorized":False})
        return 3

if __name__=="__main__":
    raise SystemExit(main())
