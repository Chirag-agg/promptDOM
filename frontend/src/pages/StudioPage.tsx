import { useState } from 'react';
import { AppLayout } from '../components/layout/AppLayout';
import { BrowserPanel } from '../components/panels/BrowserPanel';
import { PromptPanel } from '../components/panels/PromptPanel';
import { DebugPanel } from '../components/panels/DebugPanel';
import { studioApi } from '../api/client';
import type { StudioState } from '../state/studio';

export function StudioPage() {
  const [state, setState] = useState<StudioState>({
    prompt: 'Make YouTube look like X.com',
    isProcessing: false,
    result: null,
    error: null,
    referenceImages: [],
    selectedReferenceId: undefined,
  });

  const handleGenerate = async (prompt: string) => {
    setState(prev => ({ ...prev, prompt, isProcessing: true, error: null, designPlan: null, result: null }));
    try {
      const plan = await studioApi.generatePlan(prompt, state.selectedReferenceId);
      setState(prev => ({ 
        ...prev, 
        isProcessing: false,
        designPlan: plan
      }));
    } catch (err: any) {
      setState(prev => ({ ...prev, isProcessing: false, error: err.message }));
    }
  };

  const handleApply = async () => {
    if (!state.designPlan) return;
    setState(prev => ({ ...prev, isProcessing: true, error: null }));
    try {
      const response = await studioApi.applyRedesign(state.prompt, state.designPlan, state.selectedReferenceId);
      setState(prev => ({ 
        ...prev, 
        isProcessing: false,
        result: response
      }));
    } catch (err: any) {
      setState(prev => ({ ...prev, isProcessing: false, error: err.message }));
    }
  };

  return (
    <AppLayout
      leftPanel={<BrowserPanel state={state} />}
      centerPanel={
        <PromptPanel 
          state={state} 
          onGenerate={handleGenerate} 
          onApply={handleApply}
          onStateUpdate={(updates) => setState(prev => ({ ...prev, ...updates }))}
        />
      }
      rightPanel={<DebugPanel state={state} />}
    />
  );
}
