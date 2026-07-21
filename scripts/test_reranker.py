import os
from sentence_transformers import CrossEncoder

def main():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    print("Loading CrossEncoder model...")
    try:
        model = CrossEncoder(
            "mixedbread-ai/mxbai-rerank-xsmall-v1",
            device="cpu",
            cache_folder="app/ai/models"
        )
        print("Model loaded successfully!")
        
        print("Running test prediction...")
        scores = model.predict([["query", "document content"]])
        print(f"Prediction successful! Scores: {scores}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
