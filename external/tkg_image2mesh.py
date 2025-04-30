#!/usr/bin/env python3

import argparse
import os
import time
import random
import torch
from PIL import Image

from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import (
    Hunyuan3DDiTFlowMatchingPipeline,
    FaceReducer, FloaterRemover, DegenerateFaceRemover
)

def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D mesh from image using Hunyuan3D pipeline"
    )
    parser.add_argument("input_image", help="Path to input image (e.g., input.png)")
    parser.add_argument("--max-mesh-num", type=int, default=50000,
                        help="Maximum number of mesh vertices")
    parser.add_argument("--step", type=int, default=50,
                        help="Number of inference steps")
    parser.add_argument("--seed", type=int,
                        help="Random seed for mesh generation (default: random)")
    parser.add_argument("--output", required=True,
                        help="Output path for .glb file (e.g., /path/to/output.glb)")

    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    print(f"[*] Using seed: {seed}")

    image = Image.open(args.input_image)

    if image.mode == 'RGB':
        rembg = BackgroundRemover()
        image = rembg(image)

        webp_output_path = os.path.splitext(args.output)[0] + ".webp"
        image.save(webp_output_path, "WEBP")
        print(f"[✓] Exported background-removed image to: {webp_output_path}")

    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        'tencent/Hunyuan3D-2',
        subfolder='hunyuan3d-dit-v2-0',
        variant='fp16'
    )

    print("[*] Generating mesh...")
    start_time = time.time()
    mesh = pipeline(
        image=image,
        num_inference_steps=args.step,
        octree_resolution=380,
        num_chunks=20000,
        generator=torch.manual_seed(seed),
        output_type='trimesh'
    )[0]
    print(f"[+] Mesh generated in {time.time() - start_time:.2f} seconds")

    floater_remove_worker = FloaterRemover()
    degenerate_face_remove_worker = DegenerateFaceRemover()
    face_reduce_worker = FaceReducer()

    mesh = floater_remove_worker(mesh)
    mesh = degenerate_face_remove_worker(mesh)
    mesh = face_reduce_worker(mesh, args.max_mesh_num)

    mesh.export(args.output)
    print(f"[✓] Exported mesh to: {args.output}")

if __name__ == "__main__":
    main()
