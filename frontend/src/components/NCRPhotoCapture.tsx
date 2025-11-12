import React, { useRef, useState, useEffect } from 'react';
import { Camera, X, Trash2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';

interface NCRPhotoCaptureProps {
  onPhotosChange: (photos: File[]) => void;
  maxPhotos?: number;
  existingPhotos?: string[]; // URLs of existing photos
}

export const NCRPhotoCapture: React.FC<NCRPhotoCaptureProps> = ({
  onPhotosChange,
  maxPhotos = 3,
  existingPhotos = []
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isCapturing, setIsCapturing] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [photos, setPhotos] = useState<File[]>([]);
  const [photoPreviewUrls, setPhotoPreviewUrls] = useState<string[]>(existingPhotos);
  const [error, setError] = useState<string | null>(null);

  // Clean up stream on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // Update parent when photos change
  useEffect(() => {
    onPhotosChange(photos);
  }, [photos, onPhotosChange]);

  const startCamera = async () => {
    try {
      setError(null);

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' }, // Prefer back camera
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });

      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }

      setIsCapturing(true);
    } catch (err: any) {
      console.error('Failed to start camera:', err);
      setError('Failed to access camera. Please check permissions.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsCapturing(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (!context) return;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob
    canvas.toBlob((blob) => {
      if (!blob) return;

      // Create File from blob
      const timestamp = new Date().getTime();
      const file = new File([blob], `ncr-photo-${timestamp}.jpg`, {
        type: 'image/jpeg',
        lastModified: timestamp
      });

      // Create preview URL
      const previewUrl = URL.createObjectURL(blob);

      // Update state
      setPhotos(prev => [...prev, file]);
      setPhotoPreviewUrls(prev => [...prev, previewUrl]);

      // Vibrate if supported
      if ('vibrate' in navigator) {
        navigator.vibrate(100);
      }

      // If reached max photos, stop camera
      if (photos.length + 1 >= maxPhotos) {
        stopCamera();
      }
    }, 'image/jpeg', 0.9); // 90% quality
  };

  const deletePhoto = (index: number) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
    setPhotoPreviewUrls(prev => {
      // Revoke object URL to free memory
      if (prev[index] && prev[index].startsWith('blob:')) {
        URL.revokeObjectURL(prev[index]);
      }
      return prev.filter((_, i) => i !== index);
    });
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);

    if (files.length === 0) return;

    // Filter to only images
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
      setError('Please select image files only');
      return;
    }

    // Check if would exceed max photos
    if (photos.length + imageFiles.length > maxPhotos) {
      setError(`Maximum ${maxPhotos} photos allowed`);
      return;
    }

    // Create preview URLs
    const newPreviewUrls = imageFiles.map(file => URL.createObjectURL(file));

    setPhotos(prev => [...prev, ...imageFiles]);
    setPhotoPreviewUrls(prev => [...prev, ...newPreviewUrls]);
    setError(null);

    // Reset file input
    event.target.value = '';
  };

  const canAddMore = photos.length < maxPhotos;

  return (
    <div className="space-y-4">
      {/* Camera View */}
      {isCapturing && (
        <Card className="relative overflow-hidden bg-black">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-auto"
          />

          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
            <div className="flex justify-center gap-4">
              <Button
                size="lg"
                onClick={capturePhoto}
                disabled={!canAddMore}
                className="bg-white hover:bg-gray-200 text-black"
              >
                <Camera className="h-5 w-5 mr-2" />
                Capture ({photos.length}/{maxPhotos})
              </Button>

              <Button
                size="lg"
                variant="outline"
                onClick={stopCamera}
                className="bg-white/20 text-white hover:bg-white/30"
              >
                <X className="h-5 w-5 mr-2" />
                Close Camera
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Hidden canvas for photo capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Photo Gallery */}
      {photoPreviewUrls.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">
            Captured Photos ({photoPreviewUrls.length}/{maxPhotos})
          </h4>

          <div className="grid grid-cols-3 gap-2">
            {photoPreviewUrls.map((url, index) => (
              <div key={index} className="relative group">
                <img
                  src={url}
                  alt={`NCR Photo ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg border-2 border-gray-300"
                />

                <Button
                  size="icon"
                  variant="destructive"
                  onClick={() => deletePhoto(index)}
                  className="absolute top-2 right-2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>

                <div className="absolute bottom-2 left-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
                  Photo {index + 1}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {!isCapturing && canAddMore && (
        <div className="flex gap-2">
          <Button
            onClick={startCamera}
            className="flex-1"
            variant="outline"
          >
            <Camera className="h-4 w-4 mr-2" />
            Take Photo
          </Button>

          <Button
            onClick={() => fileInputRef.current?.click()}
            className="flex-1"
            variant="outline"
          >
            Upload Photo
          </Button>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      )}

      {/* Status Messages */}
      {!canAddMore && !isCapturing && (
        <Alert className="bg-green-50 border-green-500">
          <Check className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Maximum of {maxPhotos} photos captured
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="bg-red-50 border-red-500">
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Info */}
      {photoPreviewUrls.length === 0 && (
        <p className="text-sm text-gray-500 text-center">
          Capture up to {maxPhotos} photos to document the defect
        </p>
      )}
    </div>
  );
};

export default NCRPhotoCapture;
