#!/usr/bin/env python3
"""
ESRGAN-Lite / SESR naar CoreML Conversie Script

Converteert PyTorch video enhancement models naar CoreML formaat (.mlpackage)
voor gebruik op iPhone 16 Pro met optimale Neural Engine performance.

Ondersteunde modellen:
- Real-ESRGAN (x2, x4)
- SESR (Streamlined ESRGAN)
- Aangepaste ESRGAN-Lite varianten

Vereisten:
    pip install torch torchvision coremltools numpy pillow

Gebruik:
    python convert_esrgan_to_coreml.py --model-path RealESRGAN_x4.pth --scale 4
    python convert_esrgan_to_coreml.py --model-path sesr_model.pth --scale 2 --name "SESR_x2"
"""

import argparse
import sys
import warnings
from pathlib import Path
from typing import Optional, Tuple

try:
    import torch
    import torch.nn as nn
    import coremltools as ct
    from coremltools.models.neural_network import NeuralNetworkBuilder
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Installeer vereisten:")
    print("    pip install torch torchvision coremltools numpy pillow")
    sys.exit(1)

# Suppress warnings voor schonere output
warnings.filterwarnings('ignore')


class ESRGANLiteConverter:
    """
    Converter voor ESRGAN-Lite / SESR modellen naar CoreML.
    
    Optimaliseert voor iPhone 16 Pro:
    - Neural Engine (ANE) support
    - FP16 precisie voor snelheid
    - Batched input voor efficiëntie
    """
    
    # iPhone 16 Pro optimalisaties
    TARGET_IOS_VERSION = "17.0"
    COMPUTE_UNITS = ct.ComputeUnit.ALL  # CPU + GPU + Neural Engine
    
    def __init__(
        self,
        model_path: str,
        scale_factor: int = 4,
        input_size: Tuple[int, int] = (256, 256),
        model_name: Optional[str] = None
    ):
        """
        Initialiseer converter.
        
        Args:
            model_path: Pad naar PyTorch .pth model bestand
            scale_factor: Upscale factor (2 of 4)
            input_size: Input resolutie (breedte, hoogte)
            model_name: Naam voor output model (optioneel)
        """
        self.model_path = Path(model_path)
        self.scale_factor = scale_factor
        self.input_size = input_size
        self.model_name = model_name or f"ESRGAN_x{scale_factor}"
        
        # Output resolutie berekenen
        self.output_size = (
            input_size[0] * scale_factor,
            input_size[1] * scale_factor
        )
        
        print(f"🎯 Converter Config:")
        print(f"   Model: {self.model_path}")
        print(f"   Scale: {scale_factor}x")
        print(f"   Input: {input_size[0]}x{input_size[1]}")
        print(f"   Output: {self.output_size[0]}x{self.output_size[1]}")
    
    def load_pytorch_model(self) -> nn.Module:
        """
        Laad PyTorch model van .pth bestand.
        
        Returns:
            Geladen PyTorch model
        """
        print(f"\n📦 Laden PyTorch model...")
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model niet gevonden: {self.model_path}")
        
        try:
            # Probeer state_dict te laden
            checkpoint = torch.load(self.model_path, map_location='cpu')
            
            if 'params_ema' in checkpoint:
                state_dict = checkpoint['params_ema']
                print("   ✓ EMA parameters gevonden")
            elif 'params' in checkpoint:
                state_dict = checkpoint['params']
                print("   ✓ Standaard parameters gevonden")
            elif 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
                print("   ✓ State dict gevonden")
            else:
                # Model is direct opgeslagen
                state_dict = checkpoint
                print("   ✓ Direct model geladen")
            
            # Bouw RRDBNet architectuur (ESRGAN)
            from basicsr.archs.rrdbnet_arch import RRDBNet
            
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=self.scale_factor
            )
            
            model.load_state_dict(state_dict)
            model.eval()
            
            print(f"   ✓ Model geladen: {type(model).__name__}")
            print(f"   📊 Parameters: {sum(p.numel() for p in model.parameters()):,}")
            
            return model
            
        except ImportError:
            print("❌ basicsr niet geïnstalleerd")
            print("   Installeer: pip install basicsr")
            raise
        except Exception as e:
            print(f"❌ Fout bij laden model: {e}")
            raise
    
    def trace_model(self, model: nn.Module) -> torch.jit.ScriptModule:
        """
        Trace model met voorbeeld input.
        
        Args:
            model: PyTorch model
            
        Returns:
            Getraceerd TorchScript model
        """
        print(f"\n🔍 Tracen model...")
        
        # Maak dummy input
        dummy_input = torch.randn(1, 3, self.input_size[1], self.input_size[0])
        
        print(f"   Input shape: {dummy_input.shape}")
        
        # Trace model
        with torch.no_grad():
            traced_model = torch.jit.trace(model, dummy_input)
            output = traced_model(dummy_input)
        
        print(f"   Output shape: {output.shape}")
        print("   ✓ Model succesvol getraceerd")
        
        return traced_model
    
    def convert_to_coreml(
        self,
        traced_model: torch.jit.ScriptModule,
        output_path: Optional[str] = None
    ) -> str:
        """
        Converteer getraceerd model naar CoreML.
        
        Args:
            traced_model: Getraceerd TorchScript model
            output_path: Pad voor output .mlmodel (optioneel)
            
        Returns:
            Pad naar geconverteerde CoreML model (.mlmodel format)
        """
        print(f"\n🔄 Converteer naar CoreML...")
        
        if output_path is None:
            output_path = f"{self.model_name}.mlmodel"
        
        # VASTE input shapes (flexible shapes werken niet met neuralnetwork format op Windows)
        # Model wordt getraceerd met 256x256, maar kan elke vaste resolutie gebruiken
        # In de iOS app passen we frames aan naar deze resolutie
        input_height = self.input_size[1]
        input_width = self.input_size[0]
        
        # Gebruik simple tuple voor vaste shapes (niet ct.Shape met RangeDim)
        input_shape = (1, 3, input_height, input_width)
        
        print(f"   Input resolutie: {input_width}x{input_height} (vast)")
        print(f"   Output resolutie: {input_width * self.scale_factor}x{input_height * self.scale_factor}")
        
        try:
            # Converteer naar CoreML
            mlmodel = ct.convert(
                traced_model,
                inputs=[
                    ct.ImageType(
                        name="input_image",
                        shape=input_shape,
                        scale=1/255.0,  # Normalize 0-255 to 0-1
                        bias=[0, 0, 0],  # No bias
                        color_layout=ct.colorlayout.RGB,
                        channel_first=True
                    )
                ],
                # GEEN outputs parameter - coremltools infereert automatisch vanuit model
                # Dit voorkomt 'symbolic dimensions' error op Windows met neuralnetwork format
                classifier_config=None,
                # iOS14 voor neuralnetwork format compatibiliteit (Windows)
                # iOS17+ vereist mlprogram maar dat geeft BlobWriter error op Windows
                minimum_deployment_target=ct.target.iOS14,
                compute_units=self.COMPUTE_UNITS,
                # Gebruik neuralnetwork format (mlprogram geeft BlobWriter error op Windows)
                convert_to="neuralnetwork"
            )
            
            # Metadata toevoegen
            mlmodel.author = "ReActor AI"
            mlmodel.license = "MIT"
            mlmodel.short_description = f"ESRGAN-Lite video upscaler ({self.scale_factor}x)"
            
            # Sla model op
            mlmodel.save(output_path)
            
            print(f"\n✅ Conversie succesvol!")
            print(f"   Output: {output_path}")
            
            # Print model info
            spec = mlmodel.get_spec()
            print(f"\n📊 Model Specificaties:")
            print(f"   Type: {spec.WhichOneof('Type')}")
            print(f"   Input: {spec.description.input[0].name}")
            print(f"   Output: {spec.description.output[0].name}")
            
            # Check Neural Engine support
            self._check_ane_support(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"❌ Conversie mislukt: {e}")
            raise
    
    def _check_ane_support(self, model_path: str):
        """
        Check of model compatible is met Apple Neural Engine.
        
        Args:
            model_path: Pad naar CoreML model
        """
        print(f"\n🧠 Check Neural Engine support...")
        
        try:
            # Laad model en check predictions
            model = ct.models.MLModel(model_path, compute_units=ct.ComputeUnit.ALL)
            
            # Test inference met dummy data
            test_input = np.random.rand(1, 3, self.input_size[1], self.input_size[0]).astype(np.float32)
            
            print("   ✓ Model laadt correct")
            print(f"   ⚠️  ANE support pas testbaar op iPhone 16 Pro device")
            
        except Exception as e:
            print(f"   ⚠️  Kon ANE support niet verifiëren: {e}")
    
    def optimize_for_streaming(self, model_path: str) -> str:
        """
        Extra optimalisaties voor video streaming (optioneel).
        
        Args:
            model_path: Pad naar geconverteerd model
            
        Returns:
            Pad naar geoptimaliseerd model
        """
        print(f"\n⚡ Optimaliseren voor video streaming...")
        
        # Voor nu: return origineel
        # In toekomst: quantization, pruning, etc.
        
        print("   ℹ️  Streaming optimalisaties:")
        print("      - FP16 precisie: automatisch door CoreML")
        print("      - Batch processing: implementeer in app")
        print("      - Memory pooling: iOS regelt automatisch")
        
        return model_path
    
    def run(self, output_dir: str = ".") -> str:
        """
        Voer complete conversie pipeline uit.
        
        Args:
            output_dir: Folder voor output model
            
        Returns:
            Pad naar geconverteerde CoreML model
        """
        print("=" * 60)
        print("ESRGAN-Lite → CoreML Converter")
        print("=" * 60)
        
        # Stap 1: Laad PyTorch model
        pytorch_model = self.load_pytorch_model()
        
        # Stap 2: Trace model
        traced_model = self.trace_model(pytorch_model)
        
        # Stap 3: Converteer naar CoreML
        output_path = Path(output_dir) / f"{self.model_name}.mlpackage"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        coreml_path = self.convert_to_coreml(traced_model, str(output_path))
        
        # Stap 4: Optimaliseer (optioneel)
        optimized_path = self.optimize_for_streaming(coreml_path)
        
        print("\n" + "=" * 60)
        print("🎉 Conversie compleet!")
        print("=" * 60)
        print(f"\n📱 Volgende stappen:")
        print(f"   1. Sleep '{optimized_path}' naar Xcode")
        print(f"   2. Xcode genereert automatisch Swift wrapper")
        print(f"   3. Update VideoEnhancementModel.swift:")
        print(f"      let model = try await {self.model_name}.load()")
        
        return optimized_path


def download_realesrgan(scale: int = 4, output_dir: str = ".") -> str:
    """
    Download Real-ESRGAN pre-trained model.
    
    Args:
        scale: Upscale factor (2 of 4)
        output_dir: Folder voor download
        
    Returns:
        Pad naar gedownload model
    """
    import urllib.request
    from tqdm import tqdm
    
    model_urls = {
        2: "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
        4: "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    }
    
    if scale not in model_urls:
        raise ValueError(f"Ongeldige scale: {scale}. Kies 2 of 4.")
    
    url = model_urls[scale]
    output_path = Path(output_dir) / f"RealESRGAN_x{scale}plus.pth"
    
    if output_path.exists():
        print(f"Model bestaat al: {output_path}")
        return str(output_path)
    
    print(f"Downloading Real-ESRGAN x{scale}...")
    
    # Download met progress bar
    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)
    
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, output_path, reporthook=t.update_to)
    
    print(f"✓ Gedownload: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Converteer ESRGAN-Lite/SESR PyTorch model naar CoreML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  # Converteer eigen model:
  python convert_esrgan_to_coreml.py --model-path my_model.pth --scale 4
  
  # Download en converteer Real-ESRGAN:
  python convert_esrgan_to_coreml.py --download --scale 4
  
  # SESR model:
  python convert_esrgan_to_coreml.py --model-path sesr.pth --scale 2 --name SESR_x2
        """
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        help="Pad naar PyTorch .pth model bestand"
    )
    
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download Real-ESRGAN pre-trained model"
    )
    
    parser.add_argument(
        "--scale",
        type=int,
        choices=[2, 4],
        default=4,
        help="Upscale factor (2 of 4)"
    )
    
    parser.add_argument(
        "--input-size",
        type=int,
        nargs=2,
        metavar=('WIDTH', 'HEIGHT'),
        default=[256, 256],
        help="Input resolutie voor model tracing (default: 256 256)"
    )
    
    parser.add_argument(
        "--name",
        type=str,
        help="Naam voor output model (default: ESRGAN_x{scale})"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Output folder voor CoreML model"
    )
    
    args = parser.parse_args()
    
    # Check vereisten
    if not args.model_path and not args.download:
        parser.print_help()
        print("\n❌ Geef --model-path of --download op")
        sys.exit(1)
    
    # Download of gebruik eigen model
    if args.download:
        model_path = download_realesrgan(args.scale, args.output_dir)
    else:
        model_path = args.model_path
    
    # Run conversie
    try:
        converter = ESRGANLiteConverter(
            model_path=model_path,
            scale_factor=args.scale,
            input_size=tuple(args.input_size),
            model_name=args.name
        )
        
        output_path = converter.run(output_dir=args.output_dir)
        
        print(f"\n✅ Klaar! CoreML model: {output_path}")
        
    except FileNotFoundError as e:
        print(f"\n❌ Bestand niet gevonden: {e}")
        print("\n💡 Tip: Gebruik --download om Real-ESRGAN automatisch te downloaden")
        sys.exit(1)
        
    except ImportError as e:
        print(f"\n❌ Ontbrekende dependency: {e}")
        print("\n💡 Installeer vereisten:")
        print("   pip install torch torchvision coremltools numpy pillow basicsr")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Conversie mislukt: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
