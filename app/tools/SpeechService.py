from praisonai_tools import BaseTool

class SpeechService(BaseTool):
    name = "SpeechService"
    description = "Transcribes speech and generates realistic TTS."

    def _run(self, main):
        return f"Handled speech input: {main}"
