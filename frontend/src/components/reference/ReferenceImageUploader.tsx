import { useState, useCallback } from 'react';
import { UploadCloud } from 'lucide-react';
import type { ReferenceImage } from '../../state/studio';

interface UploaderProps {
  onUpload: (image: ReferenceImage) => void;
}

export function ReferenceImageUploader({ onUpload }: UploaderProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const processFile = (file: File) => {
    if (!file.type.match(/^image\/(jpeg|png|webp)$/)) {
      alert('Only PNG, JPG, and WebP images are supported.');
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      onUpload({
        id: Math.random().toString(36).substring(7),
        file,
        previewUrl,
        width: img.width,
        height: img.height
      });
    };
    img.src = previewUrl;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  }, [onUpload]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div 
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 hover:border-slate-500 bg-slate-900'}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => document.getElementById('reference-upload')?.click()}
    >
      <input 
        id="reference-upload" 
        type="file" 
        className="hidden" 
        accept="image/png, image/jpeg, image/webp" 
        onChange={handleChange}
      />
      <UploadCloud size={48} className={`mx-auto mb-4 ${isDragging ? 'text-blue-400' : 'text-slate-500'}`} />
      <h3 className="text-lg font-medium text-slate-200 mb-1">Upload Reference Image</h3>
      <p className="text-sm text-slate-400">Drag and drop or click to browse</p>
      <p className="text-xs text-slate-500 mt-4 mono">PNG, JPG, WebP up to 10MB</p>
    </div>
  );
}
