from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import time
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins='http://localhost:5173',
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def process_step(step_id: int, delay: int = 2) -> bool:
    """
    Simulasi proses yang berjalan untuk setiap langkah
    Dalam implementasi nyata, ini akan melakukan operasi yang sebenarnya
    """
    # Simulasi proses - ganti dengan logika bisnis sebenarnya
    await asyncio.sleep(delay)

    # Simulasi berhasil/gagal (di sini selalu berhasil, Anda bisa tambahkan logika untuk gagal)
    return True

async def process_generator():
    """
    Generator untuk mengirim events saat setiap langkah diproses
    """
    steps = [
        {"id": 1, "name": "Validasi Input", "delay": 1},
        {"id": 2, "name": "Proses Data", "delay": 3},
        {"id": 3, "name": "Simpan ke Database", "delay": 2},
        {"id": 4, "name": "Kirim Notifikasi", "delay": 1},
    ]

    try:
        for step in steps:
            # Kirim update bahwa langkah ini sedang diproses
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "step_update",
                    "step_id": step["id"],
                    "status": "processing"
                })
            }

            # Tunggu sebentar agar frontend dapat menampilkan status "processing"
            await asyncio.sleep(0.5)

            # Eksekusi langkah
            success = await process_step(step["id"], step["delay"])

            # Kirim hasilnya
            if success:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "step_update",
                        "step_id": step["id"],
                        "status": "completed"
                    })
                }
            else:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "step_update",
                        "step_id": step["id"],
                        "status": "failed"
                    })
                }

                # Jika ada kegagalan, kirim error dan berhenti
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "error",
                        "message": f"Proses gagal pada langkah: {step['name']}"
                    })
                }
                return

        # Semua langkah berhasil, kirim notifikasi selesai
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "process_complete",
                "message": "Semua proses berhasil diselesaikan"
            })
        }
    except Exception as e:
        # Tangani error tak terduga
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "error",
                "message": f"Error tak terduga: {str(e)}"
            })
        }

@app.get("/api/process")
async def run_process():
    """
    Endpoint untuk memulai proses dan mengirim SSE updates
    """
    return EventSourceResponse(process_generator())

# Untuk testing, tambahkan endpoint untuk memulai proses dengan skenario kegagalan
@app.get("/api/process-with-error")
async def run_process_with_error():
    """
    Endpoint untuk testing skenario kegagalan
    """
    async def error_generator():
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "step_update",
                "step_id": 1,
                "status": "processing"
            })
        }
        await asyncio.sleep(1)
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "step_update",
                "step_id": 1,
                "status": "completed"
            })
        }

        # Simulasi error pada langkah kedua
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "step_update",
                "step_id": 2,
                "status": "processing"
            })
        }
        await asyncio.sleep(1)
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "step_update",
                "step_id": 2,
                "status": "failed"
            })
        }
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "error",
                "message": "Data tidak valid untuk diproses"
            })
        }

    return EventSourceResponse(error_generator())
