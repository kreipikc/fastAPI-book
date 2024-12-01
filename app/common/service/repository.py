from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from app.common.database.database import BookOrm, new_session
from app.common.schemas.book_schemas import SBook
from app.common.database.redis import set_data_redis, get_data_redis


class BookRepository:
    @classmethod
    async def db_add_one(cls, data: SBook) -> int:
        async with new_session() as session:
            book_dict = data.model_dump()
            # Можно указывать явно -> BookOrm(name=book_dict["name"], и т.д.)
            book = BookOrm(**book_dict)
            session.add(book)       # Добавить изменения
            await session.flush()   # Отправит изменение, не завершая транзакцию
            await session.commit()  # Сохранит все изменения в БД, завершит транзакцию
            return book.id

    @classmethod
    async def db_get_all(cls):
        async with new_session() as session:
            query = select(BookOrm)
            result = await session.execute(query)
            book_models = result.scalars().all()
            return book_models

    @classmethod
    async def db_get_one(cls, id_book: int):
        result = await get_data_redis(id_book)
        if result:
            return result

        async with new_session() as session:
            book = await session.get(BookOrm, id_book)
            await set_data_redis(book)
            return book

    @classmethod
    async def db_update(cls, data: SBook, id_book: int) -> bool:
        async with new_session() as session:
            stmt = update(BookOrm).where(BookOrm.id == id_book).values(**data.model_dump(exclude_unset=True))
            await session.execute(stmt)
            await session.commit()
            return True

    @classmethod
    async def db_delete(cls, id_book: int):
        async with new_session() as session:
            try:
                book = await session.get(BookOrm, id_book)
                if book:
                    await session.delete(book)
                    await session.commit()
                    return True
                else:
                    return False
            except NoResultFound:
                return NoResultFound