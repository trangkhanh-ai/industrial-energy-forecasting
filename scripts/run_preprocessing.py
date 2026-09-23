"""Execute the notebook with a fresh kernel using this Python environment."""

from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient


def main():
    root = Path(__file__).resolve().parents[1]
    path = root / "notebooks" / "01_data_preparation.ipynb"
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    client = NotebookClient(notebook, timeout=180, resources={"metadata": {"path": str(root)}})
    # Avoid accidentally using a globally registered kernel outside the active venv.
    client.create_kernel_manager()
    client.km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    client.execute()
    nbformat.write(notebook, path)
    print("Preprocessing complete: notebook outputs, processed CSVs and cycle plot updated.")


if __name__ == "__main__":
    main()
