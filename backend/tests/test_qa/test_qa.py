import requests
import time
from pathlib import Path


def read_questions(file_path):
    """Read questions from file, skipping empty lines and comments."""
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def format_chunk(chunk):
    """Format a single chunk with better readability."""
    # Format metadata as a clean list
    metadata = chunk.get("metadata", {})
    metadata_str = "\n    Metadata:"
    for key, value in metadata.items():
        if key in ["document_title", "section", "distance"]:
            metadata_str += f"\n      - {key.replace('_', ' ').title()}: {value}"

    # Truncate text if too long
    text = chunk.get("text", "")
    if len(text) > 200:
        text = text[:197] + "..."

    return f"""    Text: {text}{metadata_str}"""


def format_answer(answer_data):
    """Format the answer and its supporting chunks with better readability."""
    answer = answer_data.get("answer", "")
    chunks = answer_data.get("chunks", [])

    # Format the answer section
    result = f"Answer:\n{answer}\n"

    # Format the chunks section
    if chunks:
        result += "\nSupporting Chunks:\n"
        for i, chunk in enumerate(chunks, 1):
            result += f"\n  Chunk {i}:\n{format_chunk(chunk)}\n"

    return result


def test_chatbot():
    """Test the chatbot with questions from test_questions.txt."""
    # Get the directory of the current script
    current_dir = Path(__file__).parent

    # Construct paths relative to the script directory
    questions_file = current_dir / "test_questions.txt"
    answers_file = current_dir / "test_answers.txt"

    # Read questions
    questions = read_questions(questions_file)
    print(f"Found {len(questions)} questions to test")

    # Prepare to write answers
    with open(answers_file, "w") as f:
        for i, question in enumerate(questions, 1):
            print(f"\nTesting question {i}/{len(questions)}: {question}")

            # Format the question section
            f.write(f"Question {i}:\n{question}\n\n")

            try:
                # Send question to chatbot
                response = requests.post(
                    "http://localhost:8000/api/ask", json={"question": question}
                )
                response.raise_for_status()

                # Get and format the answer
                answer_data = response.json()
                formatted_answer = format_answer(answer_data)
                f.write(formatted_answer)

                # Add separator between questions
                f.write("\n" + "=" * 80 + "\n\n")

                # Add a small delay between requests
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                error_msg = f"Error: Failed to get answer - {str(e)}"
                print(error_msg)
                f.write(f"{error_msg}\n\n")
                f.write("=" * 80 + "\n\n")
                continue


if __name__ == "__main__":
    test_chatbot()
