import os
from sentence_transformers import CrossEncoder

def main():
    model_name = "mixedbread-ai/mxbai-rerank-xsmall-v1"
    cache_dir = "app/ai/models"
    os.makedirs(cache_dir, exist_ok=True)

    print(f"=== DOWNLOADING MODEL RERANKER: {model_name} ===")
    print(f"Cache dir: {os.path.abspath(cache_dir)}")
    print("Please wait...")
    
    try:
        model = CrossEncoder(
            model_name,
            device="cpu",
            cache_folder=cache_dir
        )
        print(">>> Model downloaded and cached successfully!")
    except Exception as e:
        print(f"Error during download: {e}")

if __name__ == "__main__":
    main()
