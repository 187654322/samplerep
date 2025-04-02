import os
import requests
from mistralai import Mistral
from google import genai
import cohere
from openai import OpenAI
import replicate

def openRouter(model, prompt_text):
    MISTRAL_API_KEY = [
        # os.getenv("OPENROUTER_API_KEY", "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"),
        os.getenv("SECONDARY_API_KEY", "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"),
        os.getenv("THIRD_API_KEY", "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"),
        os.getenv("FORTH_API_KEY", "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"),
    ]

    MISTRAL_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an AI assistant providing answers strictly based on the provided document. Use only the retrieved content."},
            {"role": "user", "content": prompt_text}
        ]
    }

    for api_key in MISTRAL_API_KEY:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(MISTRAL_API_URL, json=data, headers=headers)
            
            # If request is successful, return response
            if response.status_code == 200:
                print(response.json())
                return response.json()["choices"][0]["message"]["content"]
            
            # If authentication fails, try next key
            elif response.status_code in [401, 403]:  
                print(f"⚠️ API Key expired or unauthorized: {api_key}, trying next key...")
                continue  

            # Other errors, break out of loop
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return "Sorry, I couldn't generate an answer."

        except Exception as e:
            print(f"An error occurred: {e}")
            return "Sorry, there was an error while processing your request."

    return "All API keys failed. Please check the service availability."

def mistralai(model, prompt_text):
    api_key = os.environ["MISTRAL_API_KEY"]

    client = Mistral(api_key=api_key)

    chat_response = client.chat.complete(
        model= model,
        messages = [
            {
                "role": "user",
                "content": prompt_text,
            },
        ]
    )
    print(chat_response.choices[0].message.content)

    
def googleModels(model, prompt_text):
    client = genai.Client(api_key="AIzaSyAg_TnLiYjOunZVfHgOZ0tu4PPuFMvsCRA")

    response = client.models.generate_content(
        model=model,
        contents=prompt_text,
    )
    return response.text

def cohereAi(model, prompt_text):
    co = cohere.ClientV2("HfLJYQ9rBDMgkC3w139u26qfoKNuVh9YMIkbS7LL")
    response = co.chat(
        model=model, 
        messages=[{"role": "user", "content": prompt_text}]
    )

    return response.message.content[0].text

def openAi(model, prompt_text):
    client = OpenAI(api_key="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")

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "developer",
                "content": "You are an AI assistant providing answers strictly based on the provided document. Use only the retrieved content."
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ]
    )

    print(completion.choices[0].message.content)
    return completion.choices[0].message.content

def replicate(model, prompt_text):
    api_key = ""
    replicate.client = replicate.Client(api_token=api_key)
    response = replicate.run(model, input={"prompt":prompt_text})
    print(response)
    return response

def get_response_from_provider(model, provider, prompt_text):
    response = "Sorry, there was an error while processing your request."
    if provider == "openrouter":
        response = openRouter(model, prompt_text)
    elif provider == "mistralai":
        response = mistralai(model, prompt_text)
    elif provider == "google":
        response = googleModels(model, prompt_text)
    elif provider == "cohereAi":
        response = cohereAi(model, prompt_text)
    elif provider == "openAI":
        response = openAi(model, prompt_text)
    elif provider == "replicate":
        response = replicate(model, prompt_text)
        
    return response