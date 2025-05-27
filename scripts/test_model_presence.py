from google.cloud import aiplatform
import os

def list_available_models():
    # Initialize the Vertex AI SDK
    aiplatform.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location="us-central1"  # You can change this to your desired location
    )

    try:
        # List all available models
        models = aiplatform.Model.list()
        
        print("\nAvailable Models:")
        print("----------------")
        for model in models:
            print(f"Display Name: {model.display_name}")
            print(f"Resource Name: {model.resource_name}")
            print("----------------")

    except Exception as e:
        print(f"Error listing models: {str(e)}")

    # Let's also try listing available text models specifically
    try:
        from vertexai.language_models import TextGenerationModel
        
        # Try to get the text-bison model specifically
        try:
            model = TextGenerationModel.from_pretrained("text-bison")
            print("\ntext-bison model is available!")
        except Exception as e:
            print(f"\nError accessing text-bison: {str(e)}")

        # Try to get the Gemini model
        try:
            from vertexai.generative_models import GenerativeModel
            model = GenerativeModel("gemini-2.5-pro-preview-05-06")
            print("\ngemini-2.5-pro-preview-05-06 model is available!")
        except Exception as e:
            print(f"\nError accessing Gemini model: {str(e)}")

    except Exception as e:
        print(f"Error checking specific models: {str(e)}")

if __name__ == "__main__":
    list_available_models()
