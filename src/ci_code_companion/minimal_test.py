import os
from google.cloud import aiplatform
import vertexai # Added for Gemini
from vertexai.generative_models import GenerativeModel, Part # Added for Gemini

project_id = "ci-code-companion"  # Or load from os.getenv if .env is set
location = "us-central1"

print(f"Attempting to initialize for project: {project_id} in {location}")
# Ensure ADC is set up (run gcloud auth application-default login)
# Or, ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid service account key
# Forcing ADC for this minimal test by not setting GOOGLE_APPLICATION_CREDENTIALS here.

aiplatform.init(project=project_id, location=location)
# vertexai.init(project=project_id, location=location) # Also initialize vertexai for Gemini
print("aiplatform.init() successful.")

# Model ID for Gemini 1.5 Flash - please verify the exact ID from documentation if this fails
# Using gemini-1.5-flash-001 as a common identifier, adjust if your preview is different.
model_id = "gemini-2.5-flash-preview-05-20" 

try:
    print(f"Initializing GenerativeModel: {model_id}")
    model = GenerativeModel(model_id)
    
    prompt = "Translate to French: Hello"
    print(f"Sending prompt to Gemini model: {prompt}")
    
    response = model.generate_content(prompt)
    
    print("Prediction successful!")
    if response.candidates and response.candidates[0].content.parts:
        print(response.candidates[0].content.parts[0].text)
    else:
        print("No content found in response or response structure is different.")
        print(f"Full response: {response}")

except Exception as e:
    print(f"An error occurred: {e}")