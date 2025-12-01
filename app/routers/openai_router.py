from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from app.config import settings

router = APIRouter()

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_SETUP = (
    "you are a demo streaming avatar from HeyGen, an industry-leading AI generation product "
    "that specialize in AI avatars and videos.\n"
    "You are here to showcase how a HeyGen streaming avatar looks and talks.\n"
    "Please note you are not equipped with any specific expertise or industry knowledge yet, "
    "which is to be provided when deployed to a real customer's use case.\n"
    "Audience will try to have a conversation with you, please try answer the questions or "
    "respond their comments naturally, and concisely. - please try your best to response with "
    "short answers, limit to one sentence per response, and only answer the last question."
)

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    text: str

@router.post("/openai/complete", response_model=PromptResponse)
async def complete_prompt(request: PromptRequest):
    try:
        chat_completion = openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_SETUP},
                {"role": "user", "content": request.prompt}
            ],
            model="gpt-3.5-turbo",
        )
        
        return PromptResponse(text=chat_completion.choices[0].message.content)
        return "Hello"
    except Exception as error:
        print(f"Error calling OpenAI: {error}")
        raise HTTPException(status_code=500, detail="Error processing your request")

