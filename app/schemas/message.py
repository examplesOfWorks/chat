from datetime import datetime

from pydantic import BaseModel

class MessageCreate(BaseModel):
    recipient_id: int
    text: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    text: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
