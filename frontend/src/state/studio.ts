export interface ReferenceImage {
  id: string;
  file: File;
  previewUrl: string;
  width: number;
  height: number;
}

export interface StudioState {
  prompt: string;
  isProcessing: boolean;
  result: any | null;
  error: string | null;
  referenceImages: ReferenceImage[];
  selectedReferenceId?: string;
}
