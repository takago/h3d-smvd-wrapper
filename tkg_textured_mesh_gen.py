#!/usr/bin/env python3

import argparse
import os
import subprocess
import textwrap
import tempfile
import random
import yaml

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")
    config = load_config(CONFIG_PATH)

    HUNYUAN_DIR = config["hunyuan"]["dir"]
    CONDA_HUNYUAN = config["hunyuan"]["conda_python"]
    HUNYUAN_SCRIPT = config["hunyuan"].get("script", "tkg_image2mesh.py")

    SYNCMVD_DIR = config["syncmvd"]["dir"]
    CONDA_SYNCMVD = config["syncmvd"]["conda_python"]
    SYNCMVD_SCRIPT = config["syncmvd"].get("script", "tkg_run_experiment.py")

    parser = argparse.ArgumentParser(
        prog="tkg_textured_mesh_gen.py",
        description=textwrap.dedent("""            画像から3Dメッシュを生成し，SyncMVDによる高品質な再構成を行うパイプラインツールです．

            ▼ 動作モードは2種類あります：
            [1] 画像からメッシュ生成＋SyncMVD
                → --input-image と --output-mesh を指定してください
            [2] 既存メッシュからSyncMVDのみ実行
                → --input-mesh のみを指定してください

            ※ --prompt は必須です（生成される内容の指示に使用されます）
        """),
        epilog=textwrap.dedent("""            【使用例】

            ① 画像からメッシュ生成＋SyncMVD
            -------------------------------------
            python tkg_textured_mesh_gen.py \
              --input-image input.png \
              --output-mesh output.glb \
              --prompt "a cute anime girl in school uniform"

            ② 既存メッシュ(.glb)を使ってSyncMVDのみ実行
            -------------------------------------
            python tkg_textured_mesh_gen.py \
              --input-mesh output.glb \
              --prompt "a cute anime girl in school uniform"
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--input-image", help="入力画像ファイル（例：input.png）")
    parser.add_argument("--prompt", required=True, help="正のプロンプト（※必須：生成する内容を指示します）")
    parser.add_argument("--negative-prompt", default="", help="負のプロンプト（例：ぼやけ、歪みなど除外したい要素）")
    parser.add_argument("--max-mesh-num", type=int, default=50000, help="生成メッシュの最大頂点数")
    parser.add_argument("--step", type=int, default=30, help="推論ステップ数")
    parser.add_argument("--seed", type=int, help="乱数シード（省略時はランダム）")
    parser.add_argument("--output-mesh", help="出力メッシュファイル名（例：output.glb）")
    parser.add_argument("--input-mesh", help="既存メッシュファイル（例：output.glb）")

    args = parser.parse_args()

    WORKDIR = SCRIPT_DIR
    os.makedirs(WORKDIR, exist_ok=True)

    if args.input_image and args.output_mesh:
        output_glb_path = os.path.join(WORKDIR, args.output_mesh)
        seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
        print(f"[*] Using seed: {seed}")

        subprocess.run([
            CONDA_HUNYUAN,
            os.path.join(HUNYUAN_DIR, HUNYUAN_SCRIPT),
            args.input_image,
            "--max-mesh-num", str(args.max_mesh_num),
            "--step", str(args.step),
            "--seed", str(seed),
            "--output", output_glb_path
        ], check=True)

    elif args.input_mesh and not args.input_image and not args.output_mesh:
        output_glb_path = args.input_mesh
        seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
        print(f"[*] Using seed: {seed}")
    else:
        raise ValueError("引数の組み合わせが不正です：--input-imageと--output-meshをセット、または--input-meshのみを指定してください")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", prefix="tkg_", dir="/tmp", delete=False) as tmpfile:
        SYNCMVD_CONFIG = tmpfile.name
        tmpfile.write(textwrap.dedent(f"""            output: "{WORKDIR}"
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
    finally:
        if os.path.exists(SYNCMVD_CONFIG):
            os.remove(SYNCMVD_CONFIG)
            print(f"[✓] 一時設定ファイルを削除しました: {SYNCMVD_CONFIG}")

if __name__ == "__main__":
    main()
