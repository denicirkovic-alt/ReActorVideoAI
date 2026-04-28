#!/usr/bin/env python3
"""
Simpel CoreML Conversie Script (zonder basicsr dependency)

Voor als je geen volledige ESRGAN omgeving wilt opzetten.
Gebruik dit om een placeholder model te maken voor snelle testing.

Vereisten:
    pip install torch coremltools

Gebruik:
    python convert_simple.py --scale 4
"""

import torch
import torch.nn as nn
import coremltools as ct
import argparse


class SimpleUpscaler(nn.Module):
    """
    Simpel upscaler model voor testing.
    Gebruikt interpolate + conv voor basic upscaling.
    """
    
    def __init__(self, scale_factor: int = 4):
        super().__init__()
        self.scale_factor = scale_factor
        
        # Simpel conv netwerk voor refinement na upscaling
        self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(64, 64, 3, padding=1)
        self.conv3 = nn.Conv2d(64, 3, 3, padding=1)
    
    def forward(self, x):
        # Upscale via interpolate
        x = torch.nn.functional.interpolate(
            x, 
            scale_factor=self.scale_factor,
            mode='bilinear',
            align_corners=False
        )
        
        # Refinement
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = torch.clamp(self.conv3(x), 0, 1)
        
        return x


def convert_simple_model(scale: int = 4, output_name: str = None):
    """
    Converteer simpel upscaler model naar CoreML.
    """
    if output_name is None:
        output_name = f"SimpleUpscaler_x{scale}"
    
    print(f"🎯 Maak simpel upscaler model (scale={scale}x)")
    
    # Maak model
    model = SimpleUpscaler(scale_factor=scale)
    model.eval()
    
    # Trace model
    print("🔍 Tracen model...")
    dummy_input = torch.randn(1, 3, 256, 256)
    traced = torch.jit.trace(model, dummy_input)
    
    # Test
    with torch.no_grad():
        output = traced(dummy_input)
        print(f"   Input: {dummy_input.shape}")
        print(f"   Output: {output.shape}")
    
    # Converteer naar CoreML
    print("🔄 Converteer naar CoreML...")
    print("   Format: neuralnetwork (Windows compatible)")
    print("   Target: iOS 14+")
    
    mlmodel = ct.convert(
        traced,
        inputs=[ct.ImageType(
            name="input_image",
            shape=(1, 3, 256, 256),
            scale=1/255.0,
            bias=[0,0,0],
            color_layout=ct.colorlayout.RGB,
            channel_first=True
        )],
        # GEEN outputs - auto infer
        minimum_deployment_target=ct.target.iOS14,  # iOS14 voor neuralnetwork
        compute_units=ct.ComputeUnit.ALL,
        convert_to="neuralnetwork"  # Werkt op Windows
    )
    
    # Sla op als .mlmodel (werkt op Windows)
    output_path = f"{output_name}.mlmodel"
    mlmodel.save(output_path)
    
    print(f"\n✅ Model opgeslagen: {output_path}")
    print(f"\n⚠️  Dit is een SIMPEL model voor testing!")
    print(f"   Geen echte AI - alleen interpolate + basic conv")
    print(f"\n📱 Xcode integratie:")
    print(f"   1. Sleep {output_path} naar Xcode")
    print(f"   2. Xcode converteert automatisch naar .mlpackage")
    print(f"   3. Test de workflow op iPhone 16 Pro")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Simpel CoreML converter")
    parser.add_argument("--scale", type=int, choices=[2, 4], default=4)
    parser.add_argument("--name", type=str, help="Output model naam")
    args = parser.parse_args()
    
    convert_simple_model(args.scale, args.name)


if __name__ == "__main__":
    main()
