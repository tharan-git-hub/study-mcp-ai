import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

class LLMHelper:
    def __init__(self, provider: str = None, api_key: str = None, model_name: str = None):
        """
        Initialize the LLM Helper.
        If provider/api_key are not specified, they will be loaded from the environment.
        """
        # Determine provider: command line argument / parameter > environment > default 'gemini'
        self.provider = provider or os.environ.get("LLM_PROVIDER")
        
        # Load API keys
        self.gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        
        # Override with parameter if provided
        if api_key:
            if self.provider == "openai":
                self.openai_key = api_key
            else:
                self.gemini_key = api_key
                self.provider = "gemini"  # Default to gemini if api_key provided without provider
                
        # If still no provider determined, guess based on available keys
        if not self.provider:
            if self.gemini_key:
                self.provider = "gemini"
            elif self.openai_key:
                self.provider = "openai"
            else:
                self.provider = "gemini"  # Fallback default
                
        # Resolve model name
        if model_name:
            self.model_name = model_name
        else:
            if self.provider == "openai":
                self.model_name = os.environ.get("OPENAI_MODEL_NAME") or "gpt-4o-mini"
            else:
                self.model_name = os.environ.get("GEMINI_MODEL_NAME") or "gemini-2.5-flash"

    def get_api_key(self) -> str:
        if self.provider == "openai":
            return self.openai_key
        return self.gemini_key

    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generate text response for a given prompt and optional system instructions.
        """
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError(
                f"API Key for provider '{self.provider}' is missing. "
                f"Please set GEMINI_API_KEY or OPENAI_API_KEY in your environment, .env file, or Settings UI."
            )
            
        if self.provider == "openai":
            return self._generate_openai(prompt, system_instruction, api_key)
        else:
            return self._generate_gemini(prompt, system_instruction, api_key)

    def _generate_openai(self, prompt: str, system_instruction: str, api_key: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content

    def _generate_gemini(self, prompt: str, system_instruction: str, api_key: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        config = genai.GenerationConfig(
            temperature=0.3
        )
        
        # Set up system instructions if supported by the model
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=config,
            system_instruction=system_instruction
        )
        
        response = model.generate_content(prompt)
        return response.text
