from api.models import ProdSchema
from app.db import products, database,orders
from sqlalchemy import desc, func, select

async def post(payload: ProdSchema):
    query = products.insert().values(title=payload.title, description=payload.description)
    return await database.execute(query=query)


async def get(id: int):
    query = products.select().where(id == products.c.id)
    return await database.fetch_one(query=query)


async def get_all():
    query = products.select()
    return await database.fetch_all(query=query)


async def get_product_count():
    query = select([func.count()]).select_from(products)
    return await database.fetch_val(query)

async def orders():
    query = orders.select()
    return await database.fetch_all(query=query)