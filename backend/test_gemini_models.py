#!/usr/bin/env python3
"""List available Gemini models."""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    """List available Gemini models."""
    api_key = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=api_key)
    
    print("🤖 Available Gemini models:")
    
    try:
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  ✅ {model.name}")
        
        # Try with the most common current model name
        print("\n🔍 Testing common model names:")
        test_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "gemini-pro",
            "models/gemini-pro"
        ]
        
        for model_name in test_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hello")
                print(f"  ✅ {model_name} - WORKS!")
                break
            except Exception as e:
                print(f"  ❌ {model_name} - {str(e)[:50]}...")
                
    except Exception as e:
        print(f"❌ Error listing models: {str(e)}")

if __name__ == "__main__":
    list_available_models()