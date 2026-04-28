# macOS CoreML Model Conversie Gids

## Overview

PyTorch → CoreML conversie werkt betrouwbaarder op **macOS** dan op Windows. 
Deze gids beschrijft hoe je een pretrained ESRGAN/SESR model converteert op macOS.

## Vereisten (macOS)

```bash
# 1. Installeer Python (via Homebrew of python.org)
brew install python@3.10

# 2. Installeer dependencies
pip install torch torchvision coremltools numpy pillow basicsr

# 3. Download Real-ESRGAN pretrained model
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
```

## Conversie Script (macOS Versie)

```python
#!/usr/bin/env python3
"""
ESRGAN naar CoreML conversie voor macOS
Werkt met mlprogram formaat (moderner dan neuralnetwork)
"""

import torch
import coremltools as ct
from basicsr.archs.rrdbnet_arch import RRDBNet

def convert_esrgan_macos(model_path: str, scale: int = 4):
    # Laad model
    checkpoint = torch.load(model_path, map_location='cpu')
    state_dict = checkpoint.get('params_ema', checkpoint.get('params', checkpoint))
    
    model = RRDBNet(
        num_in_ch=3, num_out_ch=3, num_feat=64,
        num_block=23, num_grow_ch=32, scale=scale
    )
    model.load_state_dict(state_dict)
    model.eval()
    
    # Trace model
    example_input = torch.randn(1, 3, 256, 256)
    traced = torch.jit.trace(model, example_input)
    
    # Converteer naar CoreML (mlprogram werkt op macOS!)
    mlmodel = ct.convert(
        traced,
        inputs=[ct.ImageType(
            name="input",
            shape=(1, 3, 256, 256),
            scale=1/255.0,
            color_layout=ct.colorlayout.RGB
        )],
        # GEEN outputs - auto infer
        minimum_deployment_target=ct.target.iOS17,  # iOS 17 voor iPhone 16 Pro
        compute_units=ct.ComputeUnit.ALL,  # CPU + GPU + Neural Engine
        convert_to="mlprogram"  # Werkt op macOS, niet op Windows
    )
    
    # Sla op als .mlpackage
    output_name = f"ESRGAN_x{scale}.mlpackage"
    mlmodel.save(output_name)
    print(f"✅ Model opgeslagen: {output_name}")
    
    return output_name

if __name__ == "__main__":
    convert_esrgan_macos("RealESRGAN_x4plus.pth", scale=4)
```

## Stap-voor-Stap Workflow

### Stap 1: Model Converteren (op macOS)

```bash
# Op Mac terminal:
cd ~/Downloads
python convert_esrgan_macos.py

# Output: ESRGAN_x4.mlpackage
```

### Stap 2: Upload naar Windows/iOS Project

```bash
# Option A: AirDrop / USB
# Kopieer ESRGAN_x4.mlpackage naar Windows machine

# Option B: Cloud
# Upload naar Google Drive / Dropbox
# Download op Windows in ReActor-UI-iOS/ folder
```

### Stap 3: Xcode Integratie (op Mac)

1. Open `ReActorVideoAI.xcodeproj` in Xcode
2. Sleep `ESRGAN_x4.mlpackage` naar Project Navigator
3. Xcode compileert model en genereert Swift wrapper
4. Build project (⌘+B)

### Stap 4: Swift Code Updaten

In `VideoEnhancementModel.swift`:

```swift
// Uncomment na model import:
let esrgan = try await ESRGAN_x4.load(configuration: configuration)
model = esrgan.model
```

## Cloud Mac Alternatieven

Als je geen fysieke Mac hebt:

| Service | Kosten | URL |
|---------|--------|-----|
| MacStadium | $99/maand | macstadium.com |
| AWS EC2 Mac | $26/day | aws.amazon.com/ec2 |
| GitHub Actions | Gratis (limiet) | github.com/actions |
| Friend's Mac | Gratis | Vraag een vriend |

## GitHub Actions Workflow (Automatisch)

`.github/workflows/convert-model.yml`:

```yaml
name: Convert ESRGAN to CoreML
on: [workflow_dispatch]
jobs:
  convert:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install torch coremltools basicsr
      - run: python convert_esrgan_macos.py
      - uses: actions/upload-artifact@v3
        with:
          name: coreml-model
          path: ESRGAN_x4.mlpackage
```

## Model Specificaties

| Eigenschap | Waarde |
|-----------|--------|
| Input | 256x256 RGB |
| Output | 1024x1024 RGB (4x upscale) |
| Format | CoreML mlprogram |
| iOS Target | 17.0+ |
| Device | iPhone 16 Pro (A18 Pro chip) |
| Neural Engine | 16-core |

## Troubleshooting

### "basicsr not found"
```bash
pip install basicsr
```

### "Model too large"
- Gebruik kleiner input formaat (192x192)
- Of: gebruik SESR (Streamlined ESRGAN) model

### "Conversion timeout"
- GitHub Actions heeft 6 uur limiet
- Grote modellen kunnen lang converteren

## Volgende Stappen

1. ✅ Converteer model op macOS
2. ✅ Importeer in Xcode
3. ✅ Test op iPhone 16 Pro
4. ⏳ Optioneel: Optimaliseer voor 1080p→4K

---

**Note:** Windows conversie is mogelijk maar problematisch (BlobWriter errors, 
format restricties). macOS is de aanbevolen route voor betrouwbare conversie.
