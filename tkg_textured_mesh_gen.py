#!/usr/bin/env python3

import argparse
import os
import subprocess
import textwrap
import tempfile
import random
import yaml
import glob

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def update_latest_symlink(base_dir, workdir, pattern="MVD_*", link_name="MVD_latest"):
    mvd_dirs = sorted(
        glob.glob(os.path.join(workdir, pattern)),
        key=os.path.getmtime,
        reverse=True
    )
    if not mvd_dirs:
        print("[!] No MVD output directories found.")
        return

    latest_dir = mvd_dirs[0]
    link_path = os.path.join(base_dir, link_name)

    if os.path.islink(link_path) or os.path.exists(link_path):
        os.remove(link_path)

    os.symlink(os.path.join("smvd_output", os.path.basename(latest_dir)), link_path)
    print(f"[✓] Created symlink: {link_path} -> smvd_output/{os.path.basename(latest_dir)}")

def main():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    H3D_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "h3d_output")  # Hunyuan3D output
    SMVD_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "smvd_output")  # SyncMVD output
    CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")

    os.makedirs(H3D_OUTPUT_DIR, exist_ok=True)
    os.makedirs(SMVD_OUTPUT_DIR, exist_ok=True)

    config = load_config(CONFIG_PATH)

    HUNYUAN_DIR = config["hunyuan"]["dir"]
    CONDA_HUNYUAN = config["hunyuan"]["conda_python"]
    HUNYUAN_SCRIPT = config["hunyuan"].get("script", "tkg_image2mesh.py")

    SYNCMVD_DIR = config["syncmvd"]["dir"]
    CONDA_SYNCMVD = config["syncmvd"]["conda_python"]
    SYNCMVD_SCRIPT = config["syncmvd"].get("script", "run_experiment.py")

    parser = argparse.ArgumentParser(
        prog="tkg_textured_mesh_gen.py",
        description="Pipeline tool to generate 3D mesh using Hunyuan3D and optionally apply SyncMVD for texture refinement.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--input-image", help="Input image file (e.g., input.png)")
    parser.add_argument("--prompt", help="Prompt to pass to SyncMVD (optional)")
    parser.add_argument("--negative-prompt", default="", help="Negative prompt for SyncMVD")
    parser.add_argument("--max-mesh-num", type=int, default=50000, help="Max number of mesh vertices")
    parser.add_argument("--step", type=int, default=30, help="Inference step count")
    parser.add_argument("--seed", type=int, help="Random seed (default: random)")
    parser.add_argument("--output-mesh", help="Output mesh filename (e.g., output.glb)")
    parser.add_argument("--input-mesh", help="Use an existing mesh file (e.g., output.glb)")

    args = parser.parse_args()

    output_glb_path = None
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    print(f"[*] Using seed: {seed}")

    if args.input_image and args.output_mesh:
        output_glb_path = os.path.join(H3D_OUTPUT_DIR, args.output_mesh)
        subprocess.run([
            CONDA_HUNYUAN,
            os.path.join(HUNYUAN_DIR, HUNYUAN_SCRIPT),
            args.input_image,
            "--max-mesh-num", str(args.max_mesh_num),
            "--step", str(args.step),
            "--seed", str(seed),
            "--output", output_glb_path
        ], check=True)

        if not args.prompt:
            print("[*] Hunyuan3D mesh generation only mode: skipping SyncMVD.")
            return

    elif args.input_mesh and args.prompt:
        output_glb_path = args.input_mesh

    else:
        raise ValueError("Invalid argument combination. Provide either (--input-image and --output-mesh) or (--input-mesh and --prompt).")

    if args.prompt and output_glb_path:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", prefix="tkg_", dir="/tmp", delete=False) as tmpfile:
            SYNCMVD_CONFIG = tmpfile.name
            tmpfile.write(textwrap.dedent(f"""\
                output: "{SMVD_OUTPUT_DIR}"
                mesh: "{output_glb_path}"
                mesh_config_relative: False
                cond_type: "depth"
                log_interval: 4
                mesh_scale: 1
                prompt: "{args.prompt}"
                negative_prompt: "{args.negative_prompt}"
                step: {args.step}
                seed: {seed}
            """))

        try:
            subprocess.run([
                CONDA_SYNCMVD,
                os.path.join(SYNCMVD_DIR, SYNCMVD_SCRIPT),
                "--config", SYNCMVD_CONFIG
            ], check=True)
            update_latest_symlink(SCRIPT_DIR, SMVD_OUTPUT_DIR)
        finally:
            if os.path.exists(SYNCMVD_CONFIG):
                os.remove(SYNCMVD_CONFIG)
                print(f"[✓] Deleted temporary config: {SYNCMVD_CONFIG}")

if __name__ == "__main__":
    main()
