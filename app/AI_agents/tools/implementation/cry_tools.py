from app.AI_agents.tools.base_tool import BaseTool
from app.ai.cry_detection import CryClassifier

class CryAnalysisTool(BaseTool):
    name = "cry_analysis_tool"
    description = "Analyze cry patterns and retrieve recommendations or soothing sound instructions."

    def _run(self, baby_id: str, audio_file: str, user_id: str):
        classifier = CryClassifier()
        prediction, confidence = classifier.predict(audio_file)
        sound = classifier.get_soothing_sound(prediction)
        return {
            "baby_id": baby_id,
            "prediction": prediction,
            "confidence": confidence,
            "soothing_sound": sound
        }
