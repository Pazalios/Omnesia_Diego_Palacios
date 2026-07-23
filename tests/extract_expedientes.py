from src.inbox_sorter.utils import read_inbox_documents, extract_expedientes
from pathlib import Path

if __name__ == "__main__":
    # Define the path to the inbox directory containing documents
    inbox_path = Path(__file__).resolve().parent.parent / "dataset" / "inbox"
    
    # Read documents from the inbox directory
    documents = read_inbox_documents(inbox_path)
    
    # Export the number expedientes found in the inbox
    expedientes = extract_expedientes(documents)

    # Print the number of expedientes found in the inbox
    print(f"Se generaron {len(expedientes)} expedientes a partir de los documentos encontrados en el directorio de entrada: {inbox_path}")

    for expediente in expedientes:
        print(f"Expediente MRN: {expediente.mrn}, Cliente: {expediente.cliente}, NIF-Cliente: {expediente.nif_cliente}")
        print(f"  Archivos por tipo:")
        for tipo, files in expediente.archivos_por_tipo.items():
            if files:
                print(f"    * {tipo}: {', '.join(files)}")
        print(f"  Archivos de otros tipos:")
        for tipo, files in expediente.archivos_otros_tipos.items():
            if files:
                print(f"    * {tipo}: {', '.join(files)}")
        print(f"  Expediente completo: {'Sí' if expediente.expediente_is_complete else 'No'}")
        print(f"  Tipos duplicados: {', '.join(expediente.duplicated_types()) if expediente.duplicated_types() else 'Ninguno'}")
        print("")