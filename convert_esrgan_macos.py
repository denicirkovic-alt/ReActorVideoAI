#!/usr/bin/env python3
"""
ESRGAN naar CoreML conversie voor macOS

Dit script werkt alleen op macOS (niet op Windows).
Gebruik dit om een .mlpackage te genereren voor iOS.

Vereisten:
    pip install torch coremltools basicsr

Gebruik:
    python convert_esrgan_macos.py --download --scale 4
"""

import argparse
import sys
import warnings
from pathlib import Path

try:
    import torch
    import coremltools as ct
    from basicsr.archs.rrdbnet_arch import RRDBNet
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Installeer: pip install torch coremltools basicsr")
    sys.exit(1)

warnings.filterwarnings('ignore')


def download_realesrgan(scale: int = 4) -> str:
    """Download Real-ESRGAN model"""
    import urllib.request
    from tqdm import tqdm
    
    urls = {
        2: "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
        4: "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    }
    
    url = urls.get(scale, urls[4])
    output_path = Path(f"RealESRGAN_x{scale}plus.pth")
    
    if output_path.exists():
        print(f"✓ Model bestaat al: {output_path}")
        return str(output_path)
    
    print(f"📥 Downloading Real-ESRGAN x{scale}...")
    
    class ProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize: self.total = tsize
            self.update(b * bsize - self.n)
    
    with ProgressBar(unit='B', unit_scale=True, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, output_path, reporthook=t.update_to)
    
    return str(output_path)


def convert_esrgan_macos(model_path: str, scale: int = 4, output_name: str = None):
    """
    Converteer ESRGAN naar CoreML op macOS.
    
    Args:
        model_path: Pad naar .pth model bestand
        scale: Upscale factor (2 of 4)
        output_name: Output naam (default: ESRGAN_x{scale})
    """
    if output_name is None:
        output_name = f"ESRGAN_x{scale}"
    
    print("=" * 60)
    print("ESRGAN → CoreML Converter (macOS)")
    print("=" * 60)
    
    # Laad model
    print(f"\n📦 Laden model: {model_path}")
    checkpoint = torch.load(model_path, map_location='cpu')
    
    if 'params_ema' in checkpoint:
        state_dict = checkpoint['params_ema']
    elif 'params' in checkpoint:
        state_dict = checkpoint['params']
    else:
        state_dict = checkpoint
    
    # Bouw RRDBNet
    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=scale
    )
    
    model.load_state_dict(state_dict)
    model.eval()
    
    num_params = sum(p.numel() for p in model.parameters())
    print(f"✓ Model geladen: {num_params:,} parameters")
    
    # Trace model
    print(f"\n🔍 Tracing model...")
    example_input = torch.randn(1, 3, 256, 256)
    traced = torch.jit.trace(model, example_input)
    
    with torch.no_grad():
        output = traced(example_input)
    
    print(f"   Input:  {example_input.shape}")
    print(f"   Output: {output.shape}")
    
    # Converteer naar CoreML
    print(f"\n🔄 Converting to CoreML...")
    print(f"   Format: mlprogram (iOS 17+)")
    print(f"   Target: iPhone 16 Pro (A18 Pro)")
    print(f"   Neural Engine: 16-core")
    
    mlmodel = ct.convert(
        traced,
        inputs=[ct.ImageType(
            name="input_image",
            shape=(1, 3, 256, 256),
            scale=1/255.0,  # Normalize 0-255 to 0-1
            bias=[0, 0, 0],
            color_layout=ct.colorlayout.RGB,
            channel_first=True
        )],
        # GEEN outputs - auto infer door CoreML
        minimum_deployment_target=ct.target.iOS17,
        compute_units=ct.ComputeUnit.ALL,  # CPU + GPU + ANE
        convert_to="mlprogram"
    )
    
    # Metadata
    mlmodel.author = "ReActor AI"
    mlmodel.license = "MIT"
    mlmodel.short_description = f"ESRGAN video upscaler ({scale}x) for iPhone 16 Pro"
    
    # Sla op
    output_path = f"{output_name}.mlpackage"
    mlmodel.save(output_path)
    
    print(f"\n✅ Conversie succesvol!")
    print(f"   Output: {output_path}")
    
    # Spec info
    spec = mlmodel.get_spec()
    print(f"\n📊 Model Specifications:")
    print(f"   Type: {spec.WhichOneof('Type')}")
    print(f"   Input: {spec.description.input[0].name}")
    print(f"   Output: {spec.description.output[0].name}")
    
    print(f"\n📱 Next Steps:")
    print(f"   1. Open ReActorVideoAI.xcodeproj in Xcode")
    print(f"   2. Drag {output_path} into project navigator")
    print(f"   3. Build project (⌘+B)")
    print(f"   4. Uncomment code in VideoEnhancementModel.swift")
    print(f"   5. Run on iPhone 16 Pro")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert ESRGAN to CoreML on macOS"
    )
    parser.add_argument("--model-path", type=str, help="Path to .pth model file")
    parser.add_argument("--download", action="store_true", help="Download Real-ESRGAN model")
    parser.add_argument("--scale", type=int, choices=[2, 4], default=4, help="Upscale factor")
    parser.add_argument("--name", type=str, help="Output model name")
    args = parser.parse_args()
    
    # Check macOS
    import platform
    if platform.system() != 'Darwin':
        print("⚠️  Warning: This script is designed for macOS.")
        print("   Windows users: Use convert_simple.py instead, or run this on a Mac.")
        print()
    
    # Get model
    if args.download:
        model_path = download_realesrgan(args.scale)
    elif args.model_path:
        model_path = args.model_path
    else:
        parser.print_help()
        print("\n❌ Error: Specify --download or --model-path")
        sys.exit(1)
    
    # Convert
    try:
        output = convert_esrgan_macos(model_path, args.scale, args.name)
        print(f"\n🎉 Success! Model ready: {output}")
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
