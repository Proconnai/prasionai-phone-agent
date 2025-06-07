from praisonai_tools import BaseTool

class TwilioService(BaseTool):
    name = "TwilioService"
    description = "Handles Twilio call flow and responses."

    def _run(self, main):
        return f"TwiML for: {main}"
