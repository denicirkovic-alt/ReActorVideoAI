# GitHub Actions iOS Build Guide

## Overview

Gebruik GitHub Actions (gratis macOS runners!) om je iOS app automatisch te bouwen zonder fysieke Mac.

## Setup

### Stap 1: GitHub Repository Maken

1. Ga naar [github.com](https://github.com)
2. Maak nieuwe repository: `ReActorVideoAI`
3. Upload je code:

```bash
# In je ReActor-UI-iOS folder
git init
git add .
git commit -m "Initial iOS app commit"
git remote add origin https://github.com/JOUW_USERNAME/ReActorVideoAI.git
git push -u origin main
```

### Stap 2: GitHub Actions Activeren

De workflow file `.github/workflows/build-ios.yml` is al aangemaakt. Bij push naar GitHub wordt deze automatisch gedetecteerd.

### Stap 3: Build Triggeren

**Optie A: Manueel (Aanbevolen voor testen)**
1. Ga naar GitHub → jouw repo → Actions tab
2. Klik "Build iOS App" workflow
3. Klik "Run workflow" dropdown
4. Klik groene "Run workflow" knop

**Optie B: Automatisch**
- Push code naar `main` branch
- Workflow start automatisch

### Stap 4: Download Resultaten

1. Wacht tot workflow klaar is (5-10 minuten)
2. Klik op de workflow run
3. Scroll naar "Artifacts" sectie
4. Download `ios-build-artifacts`

## Wat Je Krijgt

| Artifact | Bestand | Doel |
|----------|---------|------|
| iOS App | `ReActorVideoAI.app` | Simulator build |
| CoreML Model | `SimpleUpscaler_x4.mlmodel` | ML model voor import |
| Build Logs | Console output | Debug info |

## Kosten

GitHub Actions is **gratis** voor publieke repositories:
- 2,000 minuten/maand (meer dan genoeg)
- macOS runners: 10 minuten per build ≈ 200 builds/maand

Voor private repos: $0.008/minuut (nog steeds goedkoop)

## Troubleshooting

### "Xcode project not found"
```
Gebruik create_xcode_project.py om project te genereren voor push
```

### "CoreML model not found"
```
Workflow genereert model automatisch via convert_simple.py
```

### "Build failed"
```
Check build logs in GitHub Actions console
Meestal: Swift syntax error of missing import
```

## Voordeel vs Cloud Mac Diensten

| Service | Kosten | Setup | Makkelijk? |
|---------|--------|-------|-----------|
| **GitHub Actions** | Gratis | 1 push | ⭐⭐⭐⭐⭐ |
| MacStadium | $99/maand | Account + setup | ⭐⭐⭐ |
| AWS EC2 Mac | $26/day | AWS account + config | ⭐⭐ |
| Scaleway | Pay/hour | Account + SSH | ⭐⭐ |

## Alternatief: Xcode Cloud (Apple's CI)

Apple biedt ook Xcode Cloud aan (ingebouwd in Xcode):
- 25 uur/maand gratis
- Directe integratie met Xcode
- Vereist Apple Developer account ($99/jaar)

## Volgende Stappen Na Build

1. ✅ Download `.app` van GitHub Actions
2. ✅ Installeer op iOS Simulator (via Xcode op vriend's Mac)
3. ⏳ Of: gebruik TestFlight voor on-device testing
4. ⏳ Of: vraag iemand met Mac om build te signen voor device

---

**Status:** Workflow klaar. Jij hoeft alleen nog naar GitHub te pushen en "Run workflow" te klikken!
