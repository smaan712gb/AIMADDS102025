from google import genai

client = genai.Client(api_key="AIzaSyB7lAvOvhI3iNzWrDuaJa9zmOBgdsr5lyg"

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)