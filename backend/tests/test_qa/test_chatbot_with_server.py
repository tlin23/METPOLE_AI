import subprocess
import requests
import time
import sys

INPUT_FILE = "test_questions.txt"
OUTPUT_FILE = "test_answers.txt"
API_URL = "http://127.0.0.1:8000/ask"
HEALTH_URL = "http://127.0.0.1:8000/health"
SERVER_CMD = [
    sys.executable,
    "-m",
    "uvicorn",
    "backend.server:service",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
]
# If your FastAPI app is in a different file, e.g., backend.api.main:app, change above accordingly.


def start_server():
    print("Starting FastAPI server...")
    proc = subprocess.Popen(SERVER_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc


def wait_for_server(timeout=30):
    print("Waiting for server to be ready...")
    for _ in range(timeout * 2):
        try:
            resp = requests.get(HEALTH_URL, timeout=1)
            if resp.status_code == 200:
                print("Server is ready.")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print("Server did not start in time.")
    return False


def stop_server(proc):
    print("Stopping FastAPI server...")
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("Server stopped.")


def main():
    # Start server
    proc = start_server()
    try:
        if not wait_for_server():
            stop_server(proc)
            sys.exit(1)

        # Read questions
        with open(INPUT_FILE, "r") as fin:
            questions = [line.strip() for line in fin if line.strip()]

        # Ask questions and write answers
        with open(OUTPUT_FILE, "w") as fout:
            for idx, question in enumerate(questions, 1):
                payload = {"question": question, "top_k": 5}
                try:
                    resp = requests.post(API_URL, json=payload, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    fout.write(f"Q{idx}: {question}\nError: {e}\n\n")
                    continue

                fout.write(f"Q{idx}: {question}\n")
                fout.write(f"Answer: {data.get('answer', 'No answer')}\n")
                fout.write("Chunks used:\n")
                for i, chunk in enumerate(data.get("chunks", []), 1):
                    fout.write(f"  Chunk {i}: {chunk.get('text', '')}\n")
                    if chunk.get("metadata"):
                        fout.write(f"    Metadata: {chunk['metadata']}\n")
                    if chunk.get("distance") is not None:
                        fout.write(f"    Distance: {chunk['distance']}\n")
                fout.write("\n" + "=" * 60 + "\n\n")
    finally:
        stop_server(proc)


if __name__ == "__main__":
    main()
