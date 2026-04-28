# Complete Workflow: ESRGAN → CoreML → iOS App

## 📋 Overzicht

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  ESRGAN PyTorch │ ──▶ │  CoreML Model    │ ──▶ │  iOS Swift App  │
│  (pre-trained)  │     │  (.mlpackage)    │     │  (Video-AI)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
  RealESRGAN_x4.pth      ESRGAN_x4.mlpackage    VideoEnhancerService
  (Download/Custom)      (Converter script)     (Lazy loading)
```

---

## 🛠 Stap 1: Model Conversie (Windows/Mac/Linux)

### Vereisten Installeren
```bash
cd ReActor-UI-iOS

pip install torch torchvision coremltools numpy pillow basicsr
```

### ESRGAN Model Converteren
```bash
# Option A: Download en converteer Real-ESRGAN automatisch
python convert_esrgan_to_coreml.py --download --scale 4

# Option B: Converteer je eigen model
python convert_esrgan_to_coreml.py --model-path /pad/naar/jouw_model.pth --scale 4

# Output:
# ✅ ESRGAN_x4.mlpackage gegenereerd
```

---

## 🍎 Stap 2: Xcode Project Setup (Mac vereist)

### 1. Project Genereren
```bash
# Option A: Met XcodeGen (automatisch)
python create_xcode_project.py

# Option B: Handmatig
# Open Xcode → File → New → Project → iOS App
# Naam: ReActorVideoAI
```

### 2. CoreML Model Toevoegen
```
1. Open ReActorVideoAI.xcodeproj in Xcode
2. Sleep ESRGAN_x4.mlpackage naar Project Navigator (linker sidebar)
3. Xcode genereert automatisch Swift wrapper class:
   - ESRGAN_x4plus (voor 4x upscaling)
   - Met methods: prediction(input:), load(configuration:)
```

### 3. Swift Code Updaten

Open `VideoEnhancementModel.swift` en **uncomment** de ESRGAN code:

#### In `loadModel()` functie (~regel 72):
```swift
// METHODE 1 (AANBEVOLEN): Gebruik gegenereerde Swift class
let esrgan = try await ESRGAN_x4plus.load(configuration: configuration)
model = esrgan.model
```

#### In `enhance()` functie (~regel 108):
```swift
// 1. Converteer CVPixelBuffer naar CIImage
let ciImage = CIImage(cvPixelBuffer: pixelBuffer)

// 2. Scale naar input resolutie (256x256)
let inputImage = ciImage.transformed(by: ...)

// 3. Converteer naar CGImage
let context = CIContext()
let cgImage = context.createCGImage(inputImage, from: inputImage.extent)!

// 4. Maak CoreML input (ESRGAN_x4plusInput is auto-generated)
let input = ESRGAN_x4plusInput(inputImage: cgImage)

// 5. Prediction
let output = try await esrganModel.prediction(input: input)

// 6. Output verwerken
let outputCGImage = output.outputImage

// 7. Converteer terug naar CVPixelBuffer
let outputCIImage = CIImage(cgImage: outputCGImage)
context.render(outputCIImage, to: outputBuffer)
return outputBuffer
```

### 4. Build & Run
```
⌘+R in Xcode
→ Kies iPhone 16 Pro simulator of device
```

---

## 📱 Stap 3: App Testen

### Flow 1: Start Scherm
```
┌─────────────────────────┐
│      ReActor AI         │
│                         │
│  ┌─────────┐┌─────────┐ │
│  │   📷    ││   🎥    │ │
│  │ Laptop  ││ Telefoon│ │
│  │Foto-AI  ││Video-AI │ │
│  │         ││         │ │
│  └─────────┘└─────────┘ │
│                         │
└─────────────────────────┘
```

**Actie:** Tap op "Telefoon (Video-AI)" tegel

### Flow 2: Video-AI Modus
```
┌─────────────────────────┐
│ ← Telefoon (Video-AI)   │
│                         │
│  ┌─────────────────┐    │
│  │                 │    │
│  │  Video Preview  │    │
│  │                 │    │
│  └─────────────────┘    │
│  1920x1080 • 0:45     │
│                         │
│  [📁 Select Video]      │  ◄── Stap 1: Video kiezen
│                         │
│  [✨ Enhance Video]    │  ◄── Stap 2: AI pas hier!
│                         │
│  (Lazy loading:         │
│   AI model laadt pas    │
│   bij deze klik)        │
└─────────────────────────┘
```

### Flow 3: Processing
```
1. Tap "Enhance Video"
2. [VideoEnhancerService] Laad ESRGAN model (lazy)
3. [Progress: 0% → 100%]
4. Frame-by-frame processing:
   - Extract frame
   - Upscale 4x via CoreML (Neural Engine)
   - Write to output video
5. Resultaat: ✓ Video verbeterd!
```

### Flow 4: Resultaat
```
✓ Video verbeterd!
[Delen] [Opslaan in Bestanden]
```

---

## ✅ Checklist

### Vooraf (Windows/Mac)
- [ ] `convert_esrgan_to_coreml.py` gereed
- [ ] `ESRGAN_x4.mlpackage` gegenereerd
- [ ] Model bestaat in `ReActor-UI-iOS/` folder

### Xcode Setup (Mac)
- [ ] `ReActorVideoAI.xcodeproj` geopend
- [ ] `ESRGAN_x4.mlpackage` toegevoegd aan project
- [ ] Swift wrapper class gegenereerd (ESRGAN_x4plus)
- [ ] `VideoEnhancementModel.swift` geüpdatet (uncomment code)
- [ ] Build succesvol (⌘+B)

### Testing (iPhone 16 Pro)
- [ ] App start op start-scherm
- [ ] Tap "Telefoon (Video-AI)" → opent Video-AI modus
- [ ] "Select Video" → toont photo picker
- [ ] Video preview werkt
- [ ] "Enhance Video" → start processing
- [ ] Progress indicator toont voortgang
- [ ] Resultaat video opgeslagen
- [ ] "← Terug" → keert naar start-scherm

---

## 🔧 Troubleshooting

### Probleem: Model niet gevonden
```
[VideoEnhancementModel] ❌ Model niet geladen
```
**Oplossing:** 
1. Check of `ESRGAN_x4.mlpackage` in Xcode project zit
2. Check Target Membership (model moet bij app target horen)
3. Clean build folder (⌘+Shift+K) → Rebuild

### Probleem: Build error "Cannot find 'ESRGAN_x4plus'"
```
error: Cannot find 'ESRGAN_x4plus' in scope
```
**Oplossing:**
1. Xcode moet model compileren (⌘+B)
2. Check of `.mlpackage` correct is toegevoegd
3. Herstart Xcode

### Probleem: Lazy loading werkt niet
```
AI start meteen bij app start
```
**Oplossing:**
Check `VideoEnhancerService.swift`:
```swift
// ✅ Correct: Model pas laden in enhanceVideo()
func enhanceVideo(...) {
    enhancerService = VideoEnhancerService()  // Hier pas!
    await enhancerService.loadModel()          // Lazy loading
}

// ❌ Fout: Model al bij init
init() {
    loadModel()  // NIET hier!
}
```

### Probleem: Memory warning (lange video's)
```
Memory pressure detected
```
**Oplossing:**
- Verwerk video in kleinere batches
- Release model na gebruik: `enhancerService.releaseModel()`
- Gebruik `autoreleasepool` voor frame processing

---

## 📊 Performance Verwachtingen

| Device | 720p→1080p | 1080p→4K | 4K→8K |
|---------|-----------|----------|-------|
| iPhone 14 | 2-3 fps | 1 fps | N/A |
| iPhone 15 Pro | 5-8 fps | 2-3 fps | 1 fps |
| iPhone 16 Pro | 10-15 fps | 5-8 fps | 2-3 fps |

*fps = frames per second verwerkingssnelheid (niet real-time)

---

## 🎓 Volgende Stappen (After Testing)

1. **Batch Processing** - Meerdere video's in wachtrij
2. **Background Mode** - Verwerking met app in background
3. **Progress Persistence** - Voortgang bewaren bij app kill
4. **Quality Settings** - Meerdere presets (Snel/Balanced/Kwaliteit)
5. **Face Detection** - Alleen faces upscalen (video call mode)

---

**Status:** ✅ Code klaar. ⏳ Wacht op CoreML model + Xcode build.
