//
//  StartView.swift
//  ReActor Video-AI
//
//  Start scherm met tegel navigatie.
//  Twee tegels: Laptop (Foto-AI) en Telefoon (Video-AI)
//

import SwiftUI

struct StartView: View {
    @State private var selectedMode: AppMode? = nil
    
    enum AppMode: String, CaseIterable {
        case photoAI = "Laptop (Foto-AI)"
        case videoAI = "Telefoon (Video-AI)"
        
        var icon: String {
            switch self {
            case .photoAI: return "photo.fill"
            case .videoAI: return "video.fill"
            }
        }
        
        var description: String {
            switch self {
            case .photoAI:
                return "Face swap & enhance\n(Desktop AI)"
            case .videoAI:
                return "Video upscale & enhance\n(CoreML AI)"
            }
        }
        
        var color: Color {
            switch self {
            case .photoAI: return .blue
            case .videoAI: return .purple
            }
        }
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                // Header
                VStack(spacing: 8) {
                    Text("ReActor AI")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Kies een AI-tool om te starten")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 50)
                
                Spacer()
                
                // Tiles
                HStack(spacing: 20) {
                    ForEach(AppMode.allCases, id: \.self) { mode in
                        ModeTile(
                            mode: mode,
                            action: { selectedMode = mode }
                        )
                    }
                }
                .padding(.horizontal)
                
                Spacer()
                
                // Footer
                Text("Meer tools binnenkort beschikbaar")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.bottom, 30)
            }
            .navigationDestination(item: $selectedMode) { mode in
                switch mode {
                case .photoAI:
                    PhotoAIPlaceholderView()
                case .videoAI:
                    VideoAIView()
                }
            }
        }
    }
}

// MARK: - Mode Tile Component

struct ModeTile: View {
    let mode: StartView.AppMode
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 15) {
                Image(systemName: mode.icon)
                    .font(.system(size: 40))
                
                Text(mode.rawValue)
                    .font(.headline)
                    .multilineTextAlignment(.center)
                
                Text(mode.description)
                    .font(.caption)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
            }
            .frame(width: 150, height: 180)
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(mode.color.opacity(0.15))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(mode.color, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
        .foregroundColor(mode.color)
    }
}

// MARK: - Photo AI Placeholder

struct PhotoAIPlaceholderView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "photo.fill")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            
            Text("Laptop (Foto-AI)")
                .font(.title2)
                .fontWeight(.bold)
            
            Text("Gebruik de desktop app voor face-swap en foto enhancement.")
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)
                .padding(.horizontal)
            
            Spacer()
        }
        .padding()
        .navigationTitle("Foto-AI")
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - Preview

#Preview {
    StartView()
}
