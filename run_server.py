import sys
import asyncio
import uvicorn
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # Configure LLM Provider explicitly as requested
    os.environ["PROMPTDOM_LLM_PROVIDER"] = "NVIDIA"
    os.environ["PROMPTDOM_LLM_NVIDIA_API_KEY"] = "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"
    
    # The Coder model (CSS/JS generation)
    os.environ["PROMPTDOM_LLM_MODEL"] = "meta/llama-3.1-405b-instruct"
    
    # The Designer model (Requires Vision to see screenshots)
    os.environ["PROMPTDOM_LLM_DESIGNER_PROVIDER"] = "NVIDIA"
    os.environ["PROMPTDOM_LLM_DESIGNER_MODEL"] = "meta/llama-3.2-90b-vision-instruct"
    
    # We must NOT use reload=True on Windows because Uvicorn's worker processes 
    # override the ProactorEventLoop policy back to SelectorEventLoop, which breaks Playwright.
    uvicorn.run("promptdom.main:app", host="127.0.0.1", port=8000, reload=False)
