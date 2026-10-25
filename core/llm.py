from google import genai
from config import load_config, get_api_key

#To get the LLM response
class LLMClient:
    def __init__(self, config_path=None):
        self.config = load_config(config_path)
        self.model = self.config["llm"]["model"]
        self.max_tokens = self.config["llm"]["max_output_tokens"]
        self.client = genai.Client(api_key=get_api_key(self.config))

    #To send query to LLM and generate response
    def ask(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "max_output_tokens": self.max_tokens,
                "thinking_config": {"thinking_level": "low"},
            },
        )
        return response.text


if __name__ == "__main__":
    llm = LLMClient()
    print(llm.ask("Say hello in one short sentence."))
