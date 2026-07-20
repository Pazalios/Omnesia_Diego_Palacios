import json
import sys
from pathlib import Path

from utils import extract_expedientes, read_inbox_documents, serialize_expedientes


def get_paths() -> Path:
    base_dir = Path(__file__).resolve().parent.parent
    default_inbox_path = base_dir / "dataset" / "inbox"

    if len(sys.argv) > 1 and sys.argv[1].strip():
        return Path(sys.argv[1])

    return default_inbox_path


def main() -> None:
    inbox_path = get_paths()
    documents = read_inbox_documents(inbox_path)
    if documents == []:
        print("No se encontraron documentos en el directorio de entrada. Por favor, asegúrese de que el directorio contenga archivos de texto válidos.")
        return

    expedientes = extract_expedientes(documents)
    print(json.dumps(serialize_expedientes(expedientes), ensure_ascii=False, indent=2))



if __name__ == "__main__":
    main()