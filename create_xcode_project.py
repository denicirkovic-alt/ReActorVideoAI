#!/usr/bin/env python3
"""
Script om Xcode project te genereren voor ReActor Video-AI.
Dit maakt een .xcodeproj folder die je kunt openen in Xcode.
"""

import os
import subprocess
import sys

PROJECT_NAME = "ReActorVideoAI"
BUNDLE_ID = "com.gourieff.reactor.videoai"

def create_directory_structure():
    """Maak project folder structuur"""
    dirs = [
        f"{PROJECT_NAME}/{PROJECT_NAME}/Views",
        f"{PROJECT_NAME}/{PROJECT_NAME}/Services",
        f"{PROJECT_NAME}/{PROJECT_NAME}/Models",
        f"{PROJECT_NAME}/{PROJECT_NAME}/Utils"
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    print(f"✓ Directory structuur aangemaakt")

def create_project_yml():
    """Maak project.yml voor XcodeGen"""
    yml_content = f"""name: {PROJECT_NAME}
targets:
  {PROJECT_NAME}:
    type: application
    platform: iOS
    deploymentTarget: "17.0"
    sources:
      - {PROJECT_NAME}
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: {BUNDLE_ID}
        INFOPLIST_FILE: {PROJECT_NAME}/Info.plist
        SWIFT_VERSION: "5.9"
        TARGETED_DEVICE_FAMILY: "1,2"  # iPhone, iPad
        SUPPORTS_MAC_DESIGNED_FOR_IPHONE_IPAD: NO
    info:
      path: {PROJECT_NAME}/Info.plist
      properties:
        CFBundleDisplayName: "ReActor Video-AI"
        CFBundleShortVersionString: "1.0.0"
        CFBundleVersion: "1"
        UILaunchStoryboardName: ""
        UISupportedInterfaceOrientations:
          - UIInterfaceOrientationPortrait
        UIApplicationSceneManifest:
          UIApplicationSupportsMultipleScenes: false
          UISceneConfigurations:
            UIWindowSceneSessionRoleApplication:
              - UISceneConfigurationName: Default Configuration
                UISceneDelegateClassName: $(PRODUCT_MODULE_NAME).SceneDelegate
"""
    
    with open("project.yml", "w") as f:
        f.write(yml_content)
    
    print("✓ project.yml aangemaakt")

def check_xcodegen():
    """Check of XcodeGen geïnstalleerd is"""
    try:
        result = subprocess.run(["xcodegen", "--version"], 
                               capture_output=True, text=True, check=True)
        print(f"✓ XcodeGen gevonden: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ XcodeGen niet gevonden")
        print("  Installeer met: brew install xcodegen")
        return False

def generate_project():
    """Genereer Xcode project"""
    if not check_xcodegen():
        print("\nAlternatief: Handmatig Xcode project aanmaken")
        print("1. Open Xcode")
        print("2. File → New → Project → iOS App")
        print(f"3. Noem het '{PROJECT_NAME}'")
        print("4. Copieer de Swift files naar het project")
        return False
    
    try:
        subprocess.run(["xcodegen", "generate", "--spec", "project.yml"], 
                      check=True, capture_output=True)
        print(f"✓ {PROJECT_NAME}.xcodeproj gegenereerd")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Generatie mislukt: {e}")
        return False

def print_next_steps():
    """Print volgende stappen"""
    print("\n" + "="*60)
    print("VOLGENDE STAPPEN:")
    print("="*60)
    print("\n1. Open het project:")
    print(f"   open {PROJECT_NAME}.xcodeproj")
    print("\n2. In Xcode:")
    print("   - Selecteer je Development Team (voor signing)")
    print("   - Selecteer iPhone 16 Pro simulator of device")
    print("\n3. Build & Run (Cmd+R)")
    print("\n4. Test de Video-AI tegel:")
    print("   - Start app → Klik op 'Telefoon (Video-AI)'")
    print("   - Selecteer video → Klik 'Enhance Video'")
    print("\n5. CoreML Model toevoegen:")
    print("   - Converteer ESRGAN-Lite naar CoreML (.mlmodel)")
    print("   - Sleep .mlmodel naar Xcode project")
    print("   - Update VideoEnhancementModel.swift met model naam")
    print("\n" + "="*60)

def main():
    print("ReActor Video-AI - Xcode Project Generator")
    print("="*60)
    
    # Check of we in juiste directory zijn
    if not os.path.exists("ReActorVideoAI"):
        print("✗ Error: Run dit script vanuit de ReActor-UI-iOS folder")
        print("   cd ReActor-UI-iOS")
        print("   python create_xcode_project.py")
        sys.exit(1)
    
    create_directory_structure()
    create_project_yml()
    
    if generate_project():
        print_next_steps()
    else:
        print("\nHandmatige setup vereist. Zie instructies hierboven.")

if __name__ == "__main__":
    main()
