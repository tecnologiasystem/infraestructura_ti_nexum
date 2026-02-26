from __future__ import annotations
import threading
import queue
import uuid
import traceback
from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional

@dataclass
class EmailJob:
    job_id: str
    payload: Dict[str, Any]

class EmailQueue:
    def __init__(self):
        self._q: "queue.Queue[EmailJob]" = queue.Queue()
        self._status: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._started = False

    def start_worker(self, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Arranca un solo worker que procesa jobs en fila."""
        if self._started:
            return
        self._started = True

        def worker():
            print("🧵 [EMAIL] Worker iniciado (cola en fila)")
            while True:
                job = self._q.get()
                with self._lock:
                    self._status[job.job_id] = {"state": "RUNNING"}

                print(f"▶️ [EMAIL] Ejecutando job {job.job_id} payload={job.payload}")

                try:
                    result = handler(job.payload)  # función que envía correos (sync)
                    with self._lock:
                        self._status[job.job_id] = {"state": "DONE", "result": result}
                    print(f"✅ [EMAIL] Job {job.job_id} finalizado: {result}")
                except Exception as e:
                    err = f"{e}\n{traceback.format_exc()}"
                    with self._lock:
                        self._status[job.job_id] = {"state": "ERROR", "error": err}
                    print(f"❌ [EMAIL] Job {job.job_id} error: {err}")

                self._q.task_done()

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def enqueue(self, payload: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._status[job_id] = {"state": "QUEUED"}
        self._q.put(EmailJob(job_id=job_id, payload=payload))
        print(f"➕ [EMAIL] Job en cola {job_id}")
        return job_id

    def get_status(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            return self._status.get(job_id, {"state": "NOT_FOUND"})
