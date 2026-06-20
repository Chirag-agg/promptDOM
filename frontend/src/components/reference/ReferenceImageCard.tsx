import { Trash2, CheckCircle2 } from 'lucide-react';
import type { ReferenceImage } from '../../state/studio';

interface CardProps {
  image: ReferenceImage;
  isPrimary: boolean;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
}

export function ReferenceImageCard({ image, isPrimary, onSelect, onRemove }: CardProps) {
  return (
    <div 
      className={`group relative rounded-xl border overflow-hidden transition-all cursor-pointer ${isPrimary ? 'border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 'border-slate-700 hover:border-slate-500'}`}
      onClick={() => onSelect(image.id)}
    >
      <div className="aspect-video w-full bg-slate-950 relative">
        <img 
          src={image.previewUrl} 
          alt={image.file.name} 
          className="w-full h-full object-contain"
        />
        
        {isPrimary && (
          <div className="absolute top-2 left-2 bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded shadow-md flex items-center space-x-1">
            <CheckCircle2 size={12} />
            <span>PRIMARY TARGET</span>
          </div>
        )}

        <button 
          onClick={(e) => {
            e.stopPropagation();
            onRemove(image.id);
          }}
          className="absolute top-2 right-2 p-1.5 bg-slate-900/80 hover:bg-red-600 text-slate-300 hover:text-white rounded transition-colors opacity-0 group-hover:opacity-100 backdrop-blur"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <div className="p-3 bg-slate-900 border-t border-slate-800">
        <p className="text-sm font-medium text-slate-200 truncate" title={image.file.name}>
          {image.file.name}
        </p>
        <p className="text-xs text-slate-500 mono mt-1">
          {image.width} × {image.height}px • {(image.file.size / 1024 / 1024).toFixed(2)}MB
        </p>
      </div>
    </div>
  );
}
