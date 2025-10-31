from google import genai

client = genai.Client(api_key="AIzaSyDlSY-uLiJPSd2SW8pRAmBCBzt7ipnKitA

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)
