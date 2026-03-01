import asyncio
import sys
sys.path.append('/app')
import sqlalchemy as sa
from app.database import engine

HASH = "$2b$12$NM8vHFXDrGw8am1Eon4PsObvjyu94Dy.NQSwaJjEysC4gcZpVULEu"
EMAIL = "testadmin@local"

async def main():
    async with engine.begin() as conn:
        await conn.execute(sa.text("UPDATE usuarios SET password_hash = :h WHERE email = :e"), {"h": HASH, "e": EMAIL})
        await conn.commit()
    print('UPDATED')

if __name__ == '__main__':
    asyncio.run(main())
