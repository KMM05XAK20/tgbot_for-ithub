import redis
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import uuid

from ..config import Setting

router = Router(name="task_submission")

redis_client = Setting.redis_cli

def save_photo_to_redis(photo_file_id: str) -> str:
    uni_key = str(uuid.uuid4())

    redis_client.set(uni_key, photo_file_id)

    return uni_key

def get_photo_from_redis(key: str):

    redis_client.get(key)

def delete_photo_from_redis(key: str):

    redis_client.delete(key)

@router.message(lambda message: message.photo)
async def handle_photo(message: Message, state: FSMContext):
    largest = sorted(message.photo, key=lambda p: p.file_size or 0)[-1]
    file_id = largest.file_id

    redis_key = save_photo_to_redis(file_id)

    await state.update_data(redis_key=redis_key)
    await message.answer("Фото получено! Ожидайте проверки модератором.")

@router.message(lambda message: message.text == "Проверить фото")
async def check_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    redis_key = data.get("redis_key")

    if not redis_key:
        await message.answer("Нет фото для проверки.")
        return
    
    # получили фото по ключу из redis'a
    file_id = get_photo_from_redis(redis_key)

    if not file_id:
        await message.answer("Фото не найдено.")
        return
    # Отправили на модерацию
    await message.answer("Фото для проверки: ", photo=file_id)

    
    delete_photo_from_redis(redis_key)
    await message.answer("Фото проверено и удалено.")