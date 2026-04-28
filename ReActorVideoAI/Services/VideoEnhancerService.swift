//
//  VideoEnhancerService.swift
//  ReActor Video-AI
//
//  CoreML video enhancement service.
//  Model wordt alleen geladen bij eerste gebruik (lazy loading).
//

import Foundation
import AVFoundation
import CoreML
import VideoToolbox
import CoreImage

/// Service voor video enhancement met CoreML.
/// AI model wordt PAS geladen wanneer enhanceVideo() wordt aangeroepen.
actor VideoEnhancerService {
    
    // MARK: - Properties
    
    /// CoreML model - wordt lazy geladen
    private var mlModel: MLModel?
    
    /// Model configuration
    private let targetResolution: CGSize = CGSize(width: 1920, height: 1080) // 1080p output
    private let batchSize: Int = 4 // Verwerk 4 frames tegelijk voor efficiency
    
    // MARK: - Initialization
    
    /// Service wordt gemaakt ZONDER model te laden
    init() {
        print("[VideoEnhancerService] Gecreëerd - model NOG NIET geladen")
    }
    
    // MARK: - Lazy Model Loading
    
    /// Laad CoreML model alleen wanneer nodig
    private func loadModelIfNeeded() async throws {
        guard mlModel == nil else {
            print("[VideoEnhancerService] Model al geladen")
            return
        }
        
        print("[VideoEnhancerService] Laden van CoreML model...")
        
        // TODO: Vervang met daadwerkelijk CoreML model
        // Placeholder voor ESRGAN-Lite / SESR model
        
        // Optie 1: Laad uit bundle
        // guard let modelURL = Bundle.main.url(forResource: "ESRGAN_Lite", withExtension: "mlmodelc") else {
        //     throw EnhancerError.modelNotFound
        // }
        // mlModel = try MLModel(contentsOf: modelURL)
        
        // Optie 2: Compileer uit .mlmodel
        // let config = MLModelConfiguration()
        // config.computeUnits = .all // Gebruik CPU, GPU, Neural Engine
        // mlModel = try await ESRGAN_Lite.load(configuration: config).model
        
        // PLACEHOLDER: Simuleer model loading
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5s simulatie
        
        print("[VideoEnhancerService] Model geladen (PLACEHOLDER)")
        print("[VideoEnhancerService] NOTE: Vervang met echte CoreML model inlezen")
    }
    
    // MARK: - Video Enhancement
    
    /// Enhance video met AI upscaling.
    /// - Parameters:
    ///   - inputURL: URL van input video
    ///   - progressHandler: Callback voor voortgang (0.0 - 100.0)
    /// - Returns: URL van enhanced output video
    func enhanceVideo(
        inputURL: URL,
        progressHandler: @escaping (Double) -> Void
    ) async throws -> URL {
        
        // LAZY: Laad model pas hier
        try await loadModelIfNeeded()
        
        print("[VideoEnhancerService] Start video enhancement")
        print("[VideoEnhancerService] Input: \(inputURL.path)")
        
        // Setup output URL
        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("enhanced_\(UUID().uuidString).mov")
        
        // Verwerk video
        try await processVideo(
            inputURL: inputURL,
            outputURL: outputURL,
            progressHandler: progressHandler
        )
        
        print("[VideoEnhancerService] Enhancement compleet")
        print("[VideoEnhancerService] Output: \(outputURL.path)")
        
        return outputURL
    }
    
    // MARK: - Video Processing Pipeline
    
    private func processVideo(
        inputURL: URL,
        outputURL: URL,
        progressHandler: @escaping (Double) -> Void
    ) async throws {
        
        let asset = AVAsset(url: inputURL)
        
        // Haal video tracks op
        guard let videoTrack = try await asset.loadTracks(withMediaType: .video).first else {
            throw EnhancerError.noVideoTrack
        }
        
        let naturalSize = try await videoTrack.load(.naturalSize)
        let nominalFrameRate = try await videoTrack.load(.nominalFrameRate)
        let duration = try await asset.load(.duration)
        let totalFrames = Int(CMTimeGetSeconds(duration) * Double(nominalFrameRate))
        
        print("[VideoEnhancerService] Video specs:")
        print("  - Resolutie: \(naturalSize.width)x\(naturalSize.height)")
        print("  - Frame rate: \(nominalFrameRate) fps")
        print("  - Totale frames: \(totalFrames)")
        print("  - Target: \(targetResolution.width)x\(targetResolution.height)")
        
        // Setup asset reader
        let reader = try AVAssetReader(asset: asset)
        let readerOutput = AVAssetReaderTrackOutput(
            track: videoTrack,
            outputSettings: [
                kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
            ]
        )
        reader.add(readerOutput)
        reader.startReading()
        
        // Setup asset writer
        let writer = try AVAssetWriter(url: outputURL, fileType: .mov)
        
        let videoSettings: [String: Any] = [
            AVVideoCodecKey: AVVideoCodecType.hevc,
            AVVideoWidthKey: targetResolution.width,
            AVVideoHeightKey: targetResolution.height,
            AVVideoCompressionPropertiesKey: [
                AVVideoAverageBitRateKey: 10_000_000, // 10 Mbps
                AVVideoProfileLevelKey: "HEVC_Main_AutoLevel"
            ]
        ]
        
        let writerInput = AVAssetWriterInput(
            mediaType: .video,
            outputSettings: videoSettings,
            sourceFormatHint: try await videoTrack.load(.formatDescriptions).first
        )
        writerInput.expectsMediaDataInRealTime = false
        
        let pixelBufferAdaptor = AVAssetWriterInputPixelBufferAdaptor(
            assetWriterInput: writerInput,
            sourcePixelBufferAttributes: [
                kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
                kCVPixelBufferWidthKey as String: targetResolution.width,
                kCVPixelBufferHeightKey as String: targetResolution.height
            ]
        )
        
        writer.add(writerInput)
        writer.startWriting()
        writer.startSession(atSourceTime: .zero)
        
        // Process frames
        var frameCount = 0
        var currentTime = CMTime.zero
        
        // TODO: Vervang met echte CoreML inferentie
        // Nu: placeholder die frames resized
        
        while let sampleBuffer = readerOutput.copyNextSampleBuffer() {
            guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { continue }
            
            // PLACEHOLDER: Resize naar target resolutie
            // In productie: CoreML model inference hier
            let enhancedBuffer = try await enhanceFrame(pixelBuffer)
            
            // Append naar output
            if writerInput.isReadyForMoreMediaData {
                pixelBufferAdaptor.append(enhancedBuffer, withPresentationTime: currentTime)
            }
            
            frameCount += 1
            currentTime = CMTimeMake(value: Int64(frameCount), timescale: Int32(nominalFrameRate))
            
            // Progress update
            let progress = Double(frameCount) / Double(totalFrames) * 100.0
            progressHandler(progress)
            
            // Voor debug: stop na 30 frames (verwijder in productie)
            if frameCount >= 30 {
                print("[VideoEnhancerService] DEBUG: Stop na 30 frames")
                break
            }
        }
        
        // Finalize
        writerInput.markAsFinished()
        await writer.finishWriting()
        reader.cancelReading()
        
        print("[VideoEnhancerService] Verwerkt: \(frameCount) frames")
    }
    
    // MARK: - Frame Enhancement (Placeholder)
    
    /// Enhance individueel frame.
    /// PLACEHOLDER: Nu alleen resize. Vervang met CoreML inferentie.
    private func enhanceFrame(_ pixelBuffer: CVPixelBuffer) async throws -> CVPixelBuffer {
        
        // TODO: Vervang met echte CoreML inferentie:
        //
        // 1. Converteer pixelBuffer naar MLMultiArray
        // let inputArray = try pixelBuffer.toMLMultiArray()
        //
        // 2. Maak prediction
        // let input = ESRGAN_LiteInput(inputImage: inputArray)
        // let output = try await mlModel.prediction(input: input)
        //
        // 3. Converteer output terug naar pixelBuffer
        // return try output.outputImage.toPixelBuffer()
        
        // PLACEHOLDER: Simple resize via CoreImage
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        
        let scaleX = targetResolution.width / CGFloat(CVPixelBufferGetWidth(pixelBuffer))
        let scaleY = targetResolution.height / CGFloat(CVPixelBufferGetHeight(pixelBuffer))
        
        let transform = CGAffineTransform(scaleX: scaleX, y: scaleY)
        let scaledImage = ciImage.transformed(by: transform)
        
        // Maak output pixel buffer
        var outputBuffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(
            kCFAllocatorDefault,
            Int(targetResolution.width),
            Int(targetResolution.height),
            kCVPixelFormatType_32BGRA,
            nil,
            &outputBuffer
        )
        
        guard status == kCVReturnSuccess, let output = outputBuffer else {
            throw EnhancerError.pixelBufferCreationFailed
        }
        
        // Render naar output
        let context = CIContext()
        context.render(scaledImage, to: output)
        
        return output
    }
    
    // MARK: - Cleanup
    
    /// Release model uit geheugen
    func releaseModel() {
        mlModel = nil
        print("[VideoEnhancerService] Model vrijgegeven")
    }
}

// MARK: - Errors

enum EnhancerError: LocalizedError {
    case modelNotFound
    case modelLoadingFailed(Error)
    case noVideoTrack
    case pixelBufferCreationFailed
    case videoProcessingFailed(Error)
    
    var errorDescription: String? {
        switch self {
        case .modelNotFound:
            return "CoreML model niet gevonden in app bundle"
        case .modelLoadingFailed(let error):
            return "Model laden mislukt: \(error.localizedDescription)"
        case .noVideoTrack:
            return "Geen video track gevonden in input"
        case .pixelBufferCreationFailed:
            return "Kon pixel buffer niet aanmaken"
        case .videoProcessingFailed(let error):
            return "Video verwerking mislukt: \(error.localizedDescription)"
        }
    }
}

// MARK: - Helper Extensions

extension CVPixelBuffer {
    /// Converteer pixel buffer naar MLMultiArray voor CoreML input
    func toMLMultiArray() throws -> MLMultiArray {
        let width = CVPixelBufferGetWidth(self)
        let height = CVPixelBufferGetHeight(self)
        
        let array = try MLMultiArray(shape: [1, 3, NSNumber(value: height), NSNumber(value: width)], dataType: .float32)
        
        CVPixelBufferLockBaseAddress(self, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(self, .readOnly) }
        
        guard let baseAddress = CVPixelBufferGetBaseAddress(self) else {
            throw EnhancerError.pixelBufferCreationFailed
        }
        
        let bytesPerRow = CVPixelBufferGetBytesPerRow(self)
        
        // BGRA naar RGB float array
        for y in 0..<height {
            for x in 0..<width {
                let pixelOffset = y * bytesPerRow + x * 4
                let b = Float((baseAddress + pixelOffset).load(as: UInt8.self)) / 255.0
                let g = Float((baseAddress + pixelOffset + 1).load(as: UInt8.self)) / 255.0
                let r = Float((baseAddress + pixelOffset + 2).load(as: UInt8.self)) / 255.0
                
                let indexR = [0, 0, y, x] as [NSNumber]
                let indexG = [0, 1, y, x] as [NSNumber]
                let indexB = [0, 2, y, x] as [NSNumber]
                
                array[indexR] = NSNumber(value: r)
                array[indexG] = NSNumber(value: g)
                array[indexB] = NSNumber(value: b)
            }
        }
        
        return array
    }
}

extension MLMultiArray {
    /// Converteer MLMultiArray output terug naar pixel buffer
    func toPixelBuffer(width: Int, height: Int) throws -> CVPixelBuffer {
        var pixelBuffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(
            kCFAllocatorDefault,
            width,
            height,
            kCVPixelFormatType_32BGRA,
            nil,
            &pixelBuffer
        )
        
        guard status == kCVReturnSuccess, let buffer = pixelBuffer else {
            throw EnhancerError.pixelBufferCreationFailed
        }
        
        CVPixelBufferLockBaseAddress(buffer, [])
        defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
        
        guard let baseAddress = CVPixelBufferGetBaseAddress(buffer) else {
            throw EnhancerError.pixelBufferCreationFailed
        }
        
        let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)
        
        // RGB float array naar BGRA pixel buffer
        for y in 0..<height {
            for x in 0..<width {
                let r = Float(truncating: self[[0, 0, y, x] as [NSNumber]])
                let g = Float(truncating: self[[0, 1, y, x] as [NSNumber]])
                let b = Float(truncating: self[[0, 2, y, x] as [NSNumber]])
                
                let pixelOffset = y * bytesPerRow + x * 4
                
                (baseAddress + pixelOffset).storeBytes(of: UInt8(b * 255), as: UInt8.self)
                (baseAddress + pixelOffset + 1).storeBytes(of: UInt8(g * 255), as: UInt8.self)
                (baseAddress + pixelOffset + 2).storeBytes(of: UInt8(r * 255), as: UInt8.self)
                (baseAddress + pixelOffset + 3).storeBytes(of: UInt8(255), as: UInt8.self) // Alpha
            }
        }
        
        return buffer
    }
}
