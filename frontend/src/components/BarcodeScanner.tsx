import React, { useEffect, useRef, useState } from 'react';
import { BrowserMultiFormatReader, DecodeHintType, NotFoundException } from '@zxing/library';
import { X, Flashlight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface BarcodeScannerProps {
  onScan: (barcode: string) => void;
  onClose: () => void;
  title?: string;
  description?: string;
}

export const BarcodeScanner: React.FC<BarcodeScannerProps> = ({
  onScan,
  onClose,
  title = 'Scan Barcode',
  description = 'Position the barcode within the frame'
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [torchSupported, setTorchSupported] = useState(false);
  const [torchEnabled, setTorchEnabled] = useState(false);
  const codeReaderRef = useRef<BrowserMultiFormatReader | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    startScanning();
    return () => {
      stopScanning();
    };
  }, []);

  const startScanning = async () => {
    try {
      setIsScanning(true);
      setError(null);

      // Initialize barcode reader with hints
      const hints = new Map();
      hints.set(DecodeHintType.TRY_HARDER, true);
      hints.set(DecodeHintType.POSSIBLE_FORMATS, [
        // Support multiple barcode formats
        // BarcodeFormat.CODE_128,
        // BarcodeFormat.CODE_39,
        // BarcodeFormat.QR_CODE,
        // BarcodeFormat.EAN_13,
        // BarcodeFormat.EAN_8,
      ]);

      const codeReader = new BrowserMultiFormatReader(hints);
      codeReaderRef.current = codeReader;

      // Get video devices
      const videoInputDevices = await codeReader.listVideoInputDevices();

      if (videoInputDevices.length === 0) {
        throw new Error('No camera found on this device');
      }

      // Prefer back camera on mobile devices
      const selectedDeviceId = videoInputDevices.find(device =>
        device.label.toLowerCase().includes('back')
      )?.deviceId || videoInputDevices[0].deviceId;

      // Get media stream
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: selectedDeviceId,
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      streamRef.current = stream;

      // Check if torch/flashlight is supported
      const videoTrack = stream.getVideoTracks()[0];
      const capabilities = videoTrack.getCapabilities() as any;
      if (capabilities?.torch) {
        setTorchSupported(true);
      }

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      // Start decoding from video stream
      codeReader.decodeFromVideoDevice(
        selectedDeviceId,
        videoRef.current!,
        (result, err) => {
          if (result) {
            // Successfully decoded barcode
            const barcodeText = result.getText();

            // Vibrate if supported
            if ('vibrate' in navigator) {
              navigator.vibrate(200);
            }

            // Play beep sound (optional)
            playBeep();

            // Stop scanning and return result
            stopScanning();
            onScan(barcodeText);
          }

          if (err && !(err instanceof NotFoundException)) {
            console.error('Barcode scan error:', err);
          }
        }
      );

    } catch (err: any) {
      console.error('Failed to start barcode scanner:', err);
      setError(err.message || 'Failed to access camera. Please check permissions.');
      setIsScanning(false);
    }
  };

  const stopScanning = () => {
    // Stop video tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Reset code reader
    if (codeReaderRef.current) {
      codeReaderRef.current.reset();
      codeReaderRef.current = null;
    }

    setIsScanning(false);
    setTorchEnabled(false);
  };

  const toggleTorch = async () => {
    if (!streamRef.current || !torchSupported) return;

    try {
      const videoTrack = streamRef.current.getVideoTracks()[0];
      const newTorchState = !torchEnabled;

      await videoTrack.applyConstraints({
        advanced: [{ torch: newTorchState } as any]
      });

      setTorchEnabled(newTorchState);
    } catch (err) {
      console.error('Failed to toggle torch:', err);
    }
  };

  const playBeep = () => {
    // Create beep sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 800; // Frequency in Hz
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    } catch (err) {
      // Silently fail if audio not supported
      console.warn('Beep sound failed:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/80 to-transparent p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
            <p className="text-sm text-gray-300">{description}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-white hover:bg-white/20"
          >
            <X className="h-6 w-6" />
          </Button>
        </div>
      </div>

      {/* Video Stream */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Scan Frame Overlay */}
      <div className="absolute inset-0 flex items-center justify-center">
        {/* Darkened edges */}
        <div className="absolute inset-0 bg-black/40" />

        {/* Scan frame */}
        <div className="relative z-10">
          <div className="w-64 h-64 md:w-80 md:h-80 border-4 border-white rounded-lg shadow-lg">
            {/* Corner decorations */}
            <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-blue-500 rounded-tl-lg" />
            <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-blue-500 rounded-tr-lg" />
            <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-blue-500 rounded-bl-lg" />
            <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-blue-500 rounded-br-lg" />

            {/* Scanning line animation */}
            {isScanning && (
              <div className="absolute inset-0 overflow-hidden">
                <div className="h-1 bg-blue-500 animate-scan-line" />
              </div>
            )}
          </div>

          <p className="mt-4 text-center text-white text-sm">
            Align barcode within the frame
          </p>
        </div>
      </div>

      {/* Bottom Controls */}
      <div className="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-black/80 to-transparent p-6">
        <div className="flex justify-center gap-4">
          {torchSupported && (
            <Button
              variant={torchEnabled ? "default" : "outline"}
              size="lg"
              onClick={toggleTorch}
              className={torchEnabled ? "bg-yellow-500 hover:bg-yellow-600" : "bg-white/20 text-white hover:bg-white/30"}
            >
              <Flashlight className="h-5 w-5 mr-2" />
              {torchEnabled ? 'Flash On' : 'Flash Off'}
            </Button>
          )}

          <Button
            variant="outline"
            size="lg"
            onClick={onClose}
            className="bg-white/20 text-white hover:bg-white/30"
          >
            Cancel
          </Button>
        </div>

        {error && (
          <Alert className="mt-4 bg-red-500/20 border-red-500 text-white">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>

      {/* CSS for scanning line animation */}
      <style>{`
        @keyframes scan-line {
          0% {
            transform: translateY(0);
          }
          100% {
            transform: translateY(256px);
          }
        }

        @media (min-width: 768px) {
          @keyframes scan-line {
            0% {
              transform: translateY(0);
            }
            100% {
              transform: translateY(320px);
            }
          }
        }

        .animate-scan-line {
          animation: scan-line 2s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default BarcodeScanner;
