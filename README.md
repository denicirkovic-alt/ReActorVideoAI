# ReActor Video-AI (iOS)

iOS versie van de Video-AI modus voor iPhone 16 Pro.
Gebruikt CoreML voor video enhancement (ESRGAN-Lite/SESR).

## Project Structuur

```
ReActor-VideoAI/
├── ReActorVideoAIApp.swift       # App entry point
├── Views/
│   ├── StartView.swift             # Start scherm met tegels
│   ├── VideoAIView.swift           # Video-AI interface
│   └── VideoPlayerView.swift       # Video preview/resultaat
├── Services/
│   ├── VideoEnhancerService.swift  # CoreML video enhancement
│   └── VideoPickerService.swift    # Video selectie uit Bestanden
├── Models/
│   └── VideoEnhancementModel.swift # CoreML model wrapper
└── Utils/
    └── VideoProcessor.swift        # Frame extractie/samenstelling
```

## Vereisten

- iOS 17.0+
- Xcode 15.0+
- iPhone 16 Pro (voor beste performance)
- CoreML model: ESRGAN-Lite of SESR (toe te voegen in volgende stap)

## Features

- ✅ Video selectie uit Bestanden / Google Drive
- ✅ AI enhancement alleen op aanvraag (lazy loading)
- ✅ Batch verwerking (niet real-time)
- ✅ Resultaat opslaan naar Bestanden

## CoreML Model Conversie (STAP 1)

⚠️ **Belangrijk:** PyTorch → CoreML conversie werkt **betrouwbaarder op macOS** dan op Windows.
Windows geeft vaak BlobWriter/format errors. Zie `MACOS_CONVERSION.md` voor details.

### Optie A: macOS Conversie (Aanbevolen)

Converteer op Mac (of cloud Mac service):

```bash
# Op macOS terminal:
pip install torch coremltools basicsr
python convert_esrgan_macos.py  # Zie MACOS_CONVERSION.md

# Output: ESRGAN_x4.mlpackage
# Upload naar Windows, dan naar Xcode
```

### Optie B: Simpel Test Model (Werkt op Windows)

Voor snelle testing zonder ESRGAN dependencies:

```bash
# Alleen torch + coremltools nodig
pip install torch coremltools

# Maak simpel upscaler model
python convert_simple.py --scale 4

# Output: SimpleUpscaler_x4.mlmodel
```

### Model Integratie

1. **macOS:** Converteer model → `.mlpackage`
2. **Windows:** Kopieer `.mlpackage` naar project folder
3. **macOS (Xcode):** Sleep `.mlpackage` naar project navigator
4. Xcode genereert automatisch Swift wrapper class
5. Update `VideoEnhancementModel.swift`:

```swift
// Vervang placeholder met:
let esrgan = try await ESRGAN_x4.load(configuration: configuration)
model = esrgan.model
```

## Installatie

1. **CoreML model converteer** (zie hierboven)
2. Open `ReActorVideoAI.xcodeproj` in Xcode
3. Sleep `.mlpackage` naar project navigator
4. Build & run op iPhone 16 Pro simulator of device
5. Grant photo library permissions wanneer gevraagd

## Project Files

| Bestand | Beschrijving |
|---------|-------------|
| `convert_esrgan_to_coreml.py` | ESRGAN converter (Windows, experimenteel) |
| `convert_simple.py` | Simpel model converter (Windows, werkt) |
| `convert_esrgan_macos.py` | ESRGAN converter (macOS, aanbevolen) |
| `MACOS_CONVERSION.md` | macOS conversie gids |
| `create_xcode_project.py` | Xcode project generator |
| `SETUP.md` | Uitgebreide setup gids |
| `WORKFLOW.md` | Complete workflow documentatie |

## TODO (Volgende Stap)

- [x] CoreML conversie scripts ✨ NIEUW
- [ ] CoreML model (.mlpackage) integreren
- [ ] Model configuratie (input/output shapes)
- [ ] Progress indicator tijdens verwerking
- [ ] Background processing support
