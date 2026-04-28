//
//  VideoAIView.swift
//  ReActor Video-AI
//
//  Video-AI interface met "Select Video" en "Enhance Video" knoppen.
//  AI wordt alleen geladen wanneer "Enhance Video" wordt geklikt.
//

import SwiftUI
import PhotosUI
import AVKit

struct VideoAIView: View {
    @StateObject private var viewModel = VideoAIViewModel()
    
    var body: some View {
        VStack(spacing: 20) {
            // Header
            VStack(spacing: 8) {
                Image(systemName: "video.fill")
                    .font(.system(size: 40))
                    .foregroundColor(.purple)
                
                Text("Telefoon (Video-AI)")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Video enhancement met CoreML")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .padding(.top, 20)
            
            // Video Preview Area
            ZStack {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemGray6))
                
                if let videoURL = viewModel.selectedVideoURL {
                    VideoPlayer(player: AVPlayer(url: videoURL))
                        .cornerRadius(12)
                } else {
                    VStack(spacing: 10) {
                        Image(systemName: "arrow.up.doc.fill")
                            .font(.system(size: 40))
                            .foregroundColor(.secondary)
                        
                        Text("Selecteer een video")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .frame(height: 250)
            .padding(.horizontal)
            
            // Video Info
            if let info = viewModel.videoInfo {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Video Info")
                        .font(.headline)
                    
                    HStack {
                        Label("Resolutie: \(info.resolution)", systemImage: "rectangle")
                        Spacer()
                        Label("Duur: \(info.duration)", systemImage: "clock")
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
                .padding(.horizontal)
            }
            
            Spacer()
            
            // Action Buttons
            VStack(spacing: 12) {
                // Select Video Button
                PhotosPicker(
                    selection: $viewModel.selectedVideoItem,
                    matching: .videos,
                    photoLibrary: .shared()
                ) {
                    HStack {
                        Image(systemName: "photo.stack.fill")
                        Text("Selecteer Video")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
                .padding(.horizontal)
                
                // Enhance Video Button
                Button(action: { viewModel.enhanceVideo() }) {
                    HStack {
                        if viewModel.isProcessing {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .padding(.trailing, 8)
                        }
                        
                        Image(systemName: "wand.and.stars")
                        Text(viewModel.isProcessing ? "Bezig met verwerken..." : "Enhance Video")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(viewModel.canEnhance ? Color.purple : Color.gray)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
                .disabled(!viewModel.canEnhance || viewModel.isProcessing)
                .padding(.horizontal)
                
                // Result Actions (shown when complete)
                if viewModel.isComplete, let resultURL = viewModel.resultVideoURL {
                    VStack(spacing: 8) {
                        Text("✓ Video verbeterd!")
                            .font(.headline)
                            .foregroundColor(.green)
                        
                        HStack(spacing: 12) {
                            Button(action: { viewModel.shareVideo(url: resultURL) }) {
                                Label("Delen", systemImage: "square.and.arrow.up")
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 10)
                                    .background(Color.green.opacity(0.2))
                                    .foregroundColor(.green)
                                    .cornerRadius(8)
                            }
                            
                            Button(action: { viewModel.saveToFiles(url: resultURL) }) {
                                Label("Opslaan", systemImage: "folder.fill")
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 10)
                                    .background(Color.blue.opacity(0.2))
                                    .foregroundColor(.blue)
                                    .cornerRadius(8)
                            }
                        }
                    }
                    .padding(.top, 10)
                }
            }
            .padding(.bottom, 30)
        }
        .navigationTitle("Video-AI")
        .navigationBarTitleDisplayMode(.inline)
        .alert("Fout", isPresented: $viewModel.showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage)
        }
        .sheet(isPresented: $viewModel.showDocumentPicker) {
            // Document picker for saving to Files app
            DocumentPicker(url: viewModel.resultVideoURL!)
        }
    }
}

// MARK: - ViewModel

@MainActor
class VideoAIViewModel: ObservableObject {
    @Published var selectedVideoItem: PhotosPickerItem? {
        didSet { loadSelectedVideo() }
    }
    @Published var selectedVideoURL: URL?
    @Published var videoInfo: VideoInfo?
    @Published var isProcessing = false
    @Published var isComplete = false
    @Published var resultVideoURL: URL?
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var showDocumentPicker = false
    
    // LAZY: Service wordt alleen gemaakt bij enhance
    private var enhancerService: VideoEnhancerService?
    
    var canEnhance: Bool {
        selectedVideoURL != nil && !isProcessing && !isComplete
    }
    
    struct VideoInfo {
        let resolution: String
        let duration: String
        let frameRate: Float
    }
    
    // MARK: - Video Loading
    
    private func loadSelectedVideo() {
        guard let item = selectedVideoItem else { return }
        
        item.loadTransferable(type: Movie.self) { [weak self] result in
            Task { @MainActor in
                switch result {
                case .success(let movie?):
                    self?.selectedVideoURL = movie.url
                    self?.extractVideoInfo(from: movie.url)
                    self?.isComplete = false
                    self?.resultVideoURL = nil
                case .failure(let error):
                    self?.showError(message: "Kon video niet laden: \(error.localizedDescription)")
                case .success(nil):
                    break
                }
            }
        }
    }
    
    private func extractVideoInfo(from url: URL) {
        let asset = AVAsset(url: url)
        
        Task {
            do {
                let tracks = try await asset.loadTracks(withMediaType: .video)
                guard let videoTrack = tracks.first else { return }
                
                let naturalSize = try await videoTrack.load(.naturalSize)
                let nominalFrameRate = try await videoTrack.load(.nominalFrameRate)
                let duration = try await asset.load(.duration)
                
                let durationSeconds = CMTimeGetSeconds(duration)
                let minutes = Int(durationSeconds) / 60
                let seconds = Int(durationSeconds) % 60
                
                videoInfo = VideoInfo(
                    resolution: "\(Int(naturalSize.width))x\(Int(naturalSize.height))",
                    duration: "\(minutes):\(String(format: "%02d", seconds))",
                    frameRate: nominalFrameRate
                )
            } catch {
                print("Fout bij video info extractie: \(error)")
            }
        }
    }
    
    // MARK: - AI Enhancement (Lazy Loading)
    
    func enhanceVideo() {
        guard let inputURL = selectedVideoURL else { return }
        
        isProcessing = true
        isComplete = false
        
        // LAZY: Initialiseer service pas NU
        // Geen AI model geladen voor deze klik!
        enhancerService = VideoEnhancerService()
        
        Task {
            do {
                let outputURL = try await enhancerService!.enhanceVideo(
                    inputURL: inputURL,
                    progressHandler: { progress in
                        // TODO: Update progress UI
                        print("Voortgang: \(progress)%")
                    }
                )
                
                await MainActor.run {
                    self.resultVideoURL = outputURL
                    self.isProcessing = false
                    self.isComplete = true
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    self.showError(message: "Enhancement mislukt: \(error.localizedDescription)")
                }
            }
        }
    }
    
    // MARK: - Result Actions
    
    func shareVideo(url: URL) {
        let activityVC = UIActivityViewController(activityItems: [url], applicationActivities: nil)
        
        // Present from top view controller
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let rootViewController = windowScene.windows.first?.rootViewController {
            rootViewController.present(activityVC, animated: true)
        }
    }
    
    func saveToFiles(url: URL) {
        showDocumentPicker = true
    }
    
    // MARK: - Helpers
    
    private func showError(message: String) {
        errorMessage = message
        showError = true
    }
}

// MARK: - Transferable Movie

struct Movie: Transferable {
    let url: URL
    
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(contentType: .movie) { movie in
            SentTransferredFile(movie.url)
        } importing: { received in
            let copy = URL.documentsDirectory.appending(path: "video_\(UUID()).mov")
            try FileManager.default.copyItem(at: received.file, to: copy)
            return Self(url: copy)
        }
    }
}

// MARK: - Document Picker

struct DocumentPicker: UIViewControllerRepresentable {
    let url: URL
    
    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let picker = UIDocumentPickerViewController(forExporting: [url], asCopy: true)
        picker.delegate = context.coordinator
        return picker
    }
    
    func updateUIViewController(_ uiViewController: UIDocumentPickerViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator: NSObject, UIDocumentPickerDelegate {
        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            print("Video opgeslagen naar: \(urls.first?.path ?? "onbekend")")
        }
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        VideoAIView()
    }
}
