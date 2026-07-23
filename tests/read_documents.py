from src.inbox_sorter.utils import read_inbox_documents
from pathlib import Path

if __name__ == "__main__":
    # Define the path to the inbox directory containing documents
    inbox_path = Path(__file__).resolve().parent.parent / "dataset" / "inbox"
    
    # Read documents from the inbox directory
    documents = read_inbox_documents(inbox_path)
    
    # Print the number of documents found in the inbox
    print(f"Se encontraron {len(documents)} documentos en el directorio de entrada: {inbox_path}")

    # Print the details of each document found in the inbox
    for doc in documents:
        print(doc)