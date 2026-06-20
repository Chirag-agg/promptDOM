import type { ReferenceImage } from '../../state/studio';
import { ReferenceImageCard } from './ReferenceImageCard';

interface GalleryProps {
  images: ReferenceImage[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
}

export function ReferenceImageGallery({ images, selectedId, onSelect, onRemove }: GalleryProps) {
  if (!images || images.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-4 mt-6">
      {images.map(image => (
        <ReferenceImageCard 
          key={image.id}
          image={image}
          isPrimary={image.id === selectedId}
          onSelect={onSelect}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
}
