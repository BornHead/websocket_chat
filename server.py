from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI()

import aiomysql

# MySQL 연결 설정
async def create_pool():
  pool = await aiomysql.create_pool(
      host='',
      port=,
      user='',
      password='',
      db='',
      charset='utf8mb4',
      autocommit=True
  )
  return pool

# WebSocket 연결을 처리하는 함수
async def websocket_handler(websocket: WebSocket, room_id: str):
    await websocket.accept()
    while True:
        try:
            message = await websocket.receive_text()
            await save_message(room_id, "user", message)  # 메시지를 데이터베이스에 저장
            await broadcast_message(room_id, message)  # 모든 클라이언트에게 메시지 전송
        except WebSocketDisconnect:
            # 클라이언트 연결이 끊겼을 때 처리
            break


# 채팅 메시지를 데이터베이스에 저장하는 함수
async def save_message(room_id: str, user_id: str, message: str):
    pool = await create_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO messages (room_id, user_id, message) VALUES (%s, %s, %s)", (room_id, user_id, message))


async def broadcast_message(room_id: str, message: str):
    # 실패한 웹소켓을 제너레이터로 생성
    failed_websockets = (websocket for websocket in chat_room_websockets[room_id] if not await send_message(websocket, message))

    # 제너레이터를 순회하면서 실패한 웹소켓을 chat_room_websockets에서 제거
    async for failed_websocket in failed_websockets:
        try:
          chat_room_websockets[room_id].remove(failed_websocket)
        except:
            pass

async def send_message(websocket, message):
    try:
        await websocket.send_text(message)
        return True  # 메시지 전송 성공
    except Exception as e:
        # 메시지 전송 실패 (예외 발생)
        return False


# 채팅방과 해당 채팅방의 웹소켓 클라이언트들을 저장할 딕셔너리
chat_room_websockets = {}


@app.websocket("/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    if room_id not in chat_room_websockets:
        chat_room_websockets[room_id] = []
    chat_room_websockets[room_id].append(websocket)

    try:
        await websocket_handler(websocket, room_id)
    except WebSocketDisconnect:
        chat_room_websockets[room_id].remove(websocket)



import uvicorn
if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8080)
