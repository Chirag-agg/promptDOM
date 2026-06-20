import { Play, Loader2, Target } from 'lucide-react';
import { useState } from 'react';
import type { StudioState, ReferenceImage } from '../../state/studio';
import { GoalCard } from '../design/GoalCard';
import { LayoutCard } from '../design/LayoutCard';
import { ContentCard } from '../design/ContentCard';
import { VisualCard } from '../design/VisualCard';
import { CritiqueCard } from '../design/CritiqueCard';
import { ExecutionCard } from '../design/ExecutionCard';
import { ConfidenceMeter } from '../design/ConfidenceMeter';
import { ReviewChangesCard } from '../design/ReviewChangesCard';
import { ReferenceImageUploader } from '../reference/ReferenceImageUploader';
import { ReferenceImageGallery } from '../reference/ReferenceImageGallery';
import { studioApi } from '../../api/client';

export function PromptPanel({ 
  state, 
  onGenerate,
  onApply,
  onStateUpdate 
}: { 
  state: StudioState, 
  onGenerate: (prompt: string) => void,
  onApply: () => void,
  onStateUpdate?: (updates: Partial<StudioState>) => void
}) {
  const [prompt, setPrompt] = useState(state.prompt);
  const [activeTab, setActiveTab] = useState<'prompt' | 'design' | 'reference'>('prompt');

  const result = state.result;
  const designPlan = state.designPlan || result?.design_plan;

  // Mock critique and execution stats since backend doesn't return them directly yet
  const executionStats = result ? {
    cssLines: result.transformation?.css?.split('\n').length || 0,
    jsLines: result.transformation?.javascript?.split('\n').length || 0,
    targetsIdentified: result.transformation?.affected_elements?.length || 0,
    targetsGrounded: result.transformation?.affected_elements?.length || 0, // Mock
    estimatedRisk: 'Medium'
  } : null;

  const handleUpload = async (image: ReferenceImage) => {
    try {
      // Create a temporary object URL for immediate display
      const newImages = [...state.referenceImages, image];
      onStateUpdate?.({
        referenceImages: newImages,
        selectedReferenceId: state.selectedReferenceId || image.id
      });

      // Upload to backend
      const response = await studioApi.uploadReference(image.file);
      
      // Update the ID to match the backend reference_id
      onStateUpdate?.({
        referenceImages: state.referenceImages.map(img => 
          img.id === image.id ? { ...img, id: response.reference_id } : img
        ),
        selectedReferenceId: state.selectedReferenceId === image.id || !state.selectedReferenceId 
          ? response.reference_id 
          : state.selectedReferenceId
      });
    } catch (err) {
      console.error("Failed to upload reference:", err);
    }
  };

  const handleRemove = (id: string) => {
    const newImages = state.referenceImages.filter(img => img.id !== id);
    // Cleanup object URL
    const removed = state.referenceImages.find(img => img.id === id);
    if (removed) URL.revokeObjectURL(removed.previewUrl);

    onStateUpdate?.({
      referenceImages: newImages,
      selectedReferenceId: state.selectedReferenceId === id ? undefined : state.selectedReferenceId
    });
  };

  const handleSelect = (id: string) => {
    onStateUpdate?.({ selectedReferenceId: id });
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-900 border-x border-slate-800 shadow-xl z-10">
      <div className="border-b border-slate-800 bg-slate-900 shrink-0">
        <div className="flex space-x-1 px-2 pt-2">
          <Tab active={activeTab === 'prompt'} onClick={() => setActiveTab('prompt')}>Prompt</Tab>
          <Tab active={activeTab === 'design'} onClick={() => setActiveTab('design')} disabled={!designPlan}>Review Changes</Tab>
          <Tab active={activeTab === 'reference'} onClick={() => setActiveTab('reference')}>Reference Images</Tab>
        </div>
      </div>

      <div className="flex-1 p-6 flex flex-col relative overflow-hidden">
        {activeTab === 'prompt' && (
          <div className="flex-1 bg-slate-950 rounded-xl border border-slate-700 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all flex flex-col overflow-hidden shadow-inner">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="flex-1 w-full bg-transparent text-slate-200 p-4 resize-none outline-none font-sans text-lg placeholder:text-slate-600"
              placeholder="Describe the desired UI transformation..."
            />
            
            <div className="p-3 bg-slate-900 border-t border-slate-800 flex justify-between items-center shrink-0">
              <div className="flex flex-col">
                <span className="text-xs text-slate-500 mono mb-1">Shift + Enter to insert newline</span>
                {state.selectedReferenceId && (
                  <div className="flex items-center space-x-1 text-blue-400 text-xs font-semibold">
                    <Target size={12} />
                    <span>Reference Target Active</span>
                  </div>
                )}
              </div>
              <div className="flex space-x-3">
                <button 
                  onClick={() => onGenerate(prompt)}
                  disabled={state.isProcessing || !prompt.trim()}
                  className="flex items-center space-x-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-500 text-white px-6 py-2 rounded-lg font-medium transition-colors border border-slate-600"
                >
                  <span>{state.isProcessing && !state.designPlan ? 'Thinking...' : 'Generate Plan'}</span>
                  {state.isProcessing && !state.designPlan ? <Loader2 size={16} className="animate-spin" /> : null}
                </button>
                <button 
                  onClick={onApply}
                  disabled={state.isProcessing || !state.designPlan}
                  className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:border-slate-700 disabled:shadow-none text-white px-6 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-blue-900/20 active:scale-95 border border-blue-500"
                >
                  <span>{state.isProcessing && state.designPlan ? 'Applying...' : 'Apply Redesign'}</span>
                  {state.isProcessing && state.designPlan ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} fill="currentColor" />}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'design' && designPlan && (
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar pb-4">
            <GoalCard goal={designPlan.goal} reasoning={designPlan.reasoning} />
            
            <ReviewChangesCard changes={designPlan.changes} />
            
            <div className="grid grid-cols-2 gap-4">
              <LayoutCard layout={designPlan.layout_strategy} />
              <VisualCard visual={designPlan.visual_strategy} />
            </div>
            
            <ContentCard content={designPlan.content_strategy} />
            
            <ConfidenceMeter confidence={designPlan.confidence} />
            
            <CritiqueCard issues={["Potential contrast issues with dark theme", "Shorts selector may be unstable"]} />
            
            {executionStats && <ExecutionCard stats={executionStats} />}
          </div>
        )}

        {activeTab === 'reference' && (
          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar flex flex-col">
            <ReferenceImageUploader onUpload={handleUpload} />
            
            <div className="mt-8 flex-1">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4">
                Reference Targets ({state.referenceImages.length})
              </h3>
              
              <ReferenceImageGallery 
                images={state.referenceImages}
                selectedId={state.selectedReferenceId}
                onSelect={handleSelect}
                onRemove={handleRemove}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Tab({ children, active, disabled, onClick }: { children: React.ReactNode, active?: boolean, disabled?: boolean, onClick?: () => void }) {
  return (
    <button 
      disabled={disabled}
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active 
          ? 'border-blue-500 text-blue-400 bg-slate-800/50 rounded-t-lg' 
          : disabled 
            ? 'border-transparent text-slate-500 opacity-50 cursor-not-allowed'
            : 'border-transparent text-slate-400 hover:text-slate-300'
      }`}
    >
      {children}
    </button>
  );
}
