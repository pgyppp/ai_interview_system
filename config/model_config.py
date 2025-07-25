# config/model_config.py

# AI 模型配置
MODEL_CONFIG = {
    "ImageAnalysisAgent": {
        "model_name": "step-1o-turbo-vision",
        "base_url": "https://api.stepfun.com/v1"
    },
    "SpeechAnalysisAgent": {
        "model_name": "step-1o-audio",
        "base_url": "https://api.stepfun.com/v1"
    },
    "TextContentAgent": {
        "model_name": "step-1v-8k",
        "base_url": "https://api.stepfun.com/v1"
    },
    "IntegratedEvaluator": {
        "model_name": "step-2-mini",
        "base_url": "https://api.stepfun.com/v1"
    },
    "InterviewQuestionAgent": {
        "model_name": "step-2-mini",
        "base_url": "https://api.stepfun.com/v1"
    }
}