# ReActor Video-AI iOS Setup Gids

## 📁 Wat is Aangemaakt?

```
ReActor-UI-iOS/
├── README.md                           # Project overview
├── SETUP.md                            # Deze setup gids
├── create_xcode_project.py             # Script om Xcode project te genereren
└── ReActorVideoAI/
    ├── ReActorVideoAIApp.swift         # App entry point (@main)
    ├── Info.plist                      # iOS app configuratie
    ├── Views/
    │   ├── StartView.swift             # Start scherm met 2 tegels
    │   └── VideoAIView.swift           # Video-AI interface + ViewModel
    ├── Services/
    │   └── VideoEnhancerService.swift  # CoreML video enhancement (lazy loading)
    └── Models/
        └── VideoEnhancementModel.swift # CoreML model wrapper
```

## ✅ Wat Werkt Nu?

### 1. Start Scherm (2 Tegels)
- **Tegel A: "Laptop (Foto-AI)"** - Placeholder voor desktop workflow
- **Tegel B: "Telefoon (Video-AI)"** - Video enhancement modus

### 2. Video-AI Interface
- **"Selecteer Video"** knop → Photo picker (werkt)
- **Video preview** → In-app video player (werkt)
- **"Enhance Video"** knop → Triggers AI service (placeholder)
- **Progress tracking** → UI updates (placeholder)
- **Resultaat acties** → Delen / Opslaan (werkt)

### 3. Lazy Loading (BELANGRIJK!)
- ✅ Geen AI model bij app start
- ✅ Geen AI model bij openen tegel
- ✅ AI model PAS geladen wanneer "Enhance Video" geklikt

## 🛠 Setup Stappen

### Stap 1: Vereisten
- macOS met Xcode 15.0+
- iPhone 16 Pro simulator of device (iOS 17.0+)
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (optionaal, voor automatische project generatie)

### Stap 2: Project Aanmaken

#### Optie A: Automatisch (met XcodeGen)
```bash
cd ReActor-UI-iOS
python create_xcode_project.py
```

#### Optie B: Handmatig
1. Open Xcode
2. File → New → Project → iOS App
3. Configureer:
   - **Name**: `ReActorVideoAI`
   - **Team**: Jouw Apple ID
   - **Organization**: `com.gourieff`
   - **Interface**: SwiftUI
   - **Language**: Swift
   - **Minimum iOS Version**: 17.0
4. Klik "Create"
5. Copieer alle Swift files uit `ReActorVideoAI/` naar je project

### Stap 3: Build & Run
```bash
# Open project
open ReActorVideoAI.xcodeproj

# Of in Xcode:
# Cmd+R om te builden en runnen
```

## 🎯 Wat Je Nu Ziet

### Flow 1: Start Scherm
```
┌─────────────────────────┐
│      ReActor AI         │
│   Kies een AI-tool      │
│                         │
│  ┌─────┐   ┌─────┐      │
│  │ 📷  │   │ 🎥  │      │
│  │Foto │   │Video│      │
│  │ AI  │   │ AI  │      │
│  └─────┘   └─────┘      │
│                         │
│ Meer tools binnenkort   │
└─────────────────────────┘
```

### Flow 2: Video-AI Modus
```
┌─────────────────────────┐
│ ← Telefoon (Video-AI)   │
│                         │
│      ┌─────────┐        │
│      │         │        │
│      │  Video  │        │
│      │ Preview │        │
│      │         │        │
│      └─────────┘        │
│   1920x1080 • 0:42     │
│                         │
│ ┌─────────────────────┐ │
│ │  📁 Select Video    │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │  ✨ Enhance Video   │ │
│ └─────────────────────┘ │
│                         │
│ [Progress bar tijdens   │
│  verwerking]            │
│                         │
│ ✓ Video verbeterd!      │
│ [Delen] [Opslaan]       │
└─────────────────────────┘
```

## 📋 TODO Lijst (Volgende Stappen)

### Prioriteit 1: CoreML Model Toevoegen
- [ ] Converteer ESRGAN-Lite PyTorch model naar CoreML
- [ ] Voeg `.mlmodel` toe aan Xcode project
- [ ] Update `VideoEnhancementModel.loadModel()` met echte model naam
- [ ] Test frame enhancement (bypass placeholder)

### Prioriteit 2: Model Parameters
- [ ] Kies input resolutie (640x360 = snel, 1280x720 = beter)
- [ ] Kies upscale factor (2x of 4x)
- [ ] Optimaliseer voor iPhone 16 Pro Neural Engine

### Prioriteit 3: Performance
- [ ] Voeg progress indicator toe (echte %)
- [ ] Background processing support
- [ ] Cancel knop tijdens verwerking
- [ ] Geheugen management voor lange video's

### Prioriteit 4: Features
- [ ] Vergelijk before/after (split view)
- [ ] Video trimming (selecteer fragment)
- [ ] Batch processing (meerdere video's)

## 🐛 Bekende Beperkingen (Placeholder)

| Aspect | Huidig | Target |
|--------|--------|--------|
| AI Model | ❌ Placeholder (resize only) | ✅ ESRGAN-Lite CoreML |
| Upscaling | ❌ 1x (geen verbetering) | ✅ 2x of 4x |
| Quality | ❌ Basic resize | ✅ AI super-resolution |
| Speed | ⚠️ Debug (30 frame limit) | ✅ Full video |

## 🔧 CoreML Model Converteer Gids

### Van PyTorch naar CoreML

```bash
# 1. Installeer dependencies
pip install torch torchvision coremltools

# 2. Download Real-ESRGAN model
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth

# 3. Converteer script (save als convert_to_coreml.py)
python convert_to_coreml.py
```

**convert_to_coreml.py:**
```python
import torch
import coremltools as ct
from basicsr.archs.rrdbnet_arch import RRDBNet

# Laad PyTorch model
model = RRDBNet(
    num_in_ch=3, num_out_ch=3, num_feat=64,
    num_block=23, num_grow_ch=32, scale=4
)
model.load_state_dict(torch.load('RealESRGAN_x4plus.pth')['params_ema'])
model.eval()

# Trace model
example_input = torch.randn(1, 3, 256, 256)
traced_model = torch.jit.trace(model, example_input)

# Converteer naar CoreML
mlmodel = ct.convert(
    traced_model,
    inputs=[ct.ImageType(name="input", shape=(1, 3, 256, 256))],
    outputs=[ct.ImageType(name="output", shape=(1, 3, 1024, 1024))],
    minimum_deployment_target=ct.target.iOS17,
    compute_units=ct.ComputeUnit.ALL
)

# Sla op
mlmodel.save("ESRGAN_x4plus.mlmodel")
print("✓ Model geconverteerd: ESRGAN_x4plus.mlmodel")
```

### In Xcode
1. Sleep `ESRGAN_x4plus.mlmodel` naar project navigator
2. Xcode genereert automatisch `ESRGAN_x4plus` Swift class
3. Update `VideoEnhancementModel.swift`:
   ```swift
   // Vervang placeholder met:
   let esrgan = try await ESRGAN_x4plus.load(configuration: configuration)
   model = esrgan.model
   ```

## 📞 Support

Voor vragen over:
- **SwiftUI**: Apple's documentatie
- **CoreML**: [CoreML Tools](https://github.com/apple/coremltools)
- **Video processing**: [AVFoundation docs](https://developer.apple.com/documentation/avfoundation)
- **ESRGAN**: [Real-ESRGAN GitHub](https://github.com/xinntao/Real-ESRGAN)

---

**Status**: ✅ Structuur klaar. ⏳ Wacht op CoreML model.
