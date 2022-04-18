from pydantic import BaseModel, Field


class ProdSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=50)
    description: str = Field(..., min_length=3, max_length=50)


class ProdDB(ProdSchema):
    id: int

class OrderSchema(BaseModel):
    id:int
    product : int