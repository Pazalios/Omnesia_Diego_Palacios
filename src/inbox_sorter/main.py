# Import necessary phyton modules
import sys
from pathlib import Path

# Import functions from utils.py
from .utils import *


def main(inbox_path: Path, output_path: Path) -> None:
    """
    Main function to read documents from the inbox, process them into expedientes, and generate a report.
    """
    # Read documents from the inbox directory
    print(f"Leyendo archivo de la ruta de entrada: {inbox_path}")
    print("Incidencias encontradas durante la lectura de documentos:\n")
    documents = read_inbox_documents(inbox_path)
    
    # If no documents are found 
    if documents == []:
        print(f"No se encontraron documentos en el directorio de entrada: {inbox_path}")
        print("No se generará un informe de salida.")
        sys.exit(0)
    # If documents are found, process them and generate a report
    else:
        print(f"\nSe encontraron {len(documents)} documentos en el directorio de entrada")
        print("Generando expedientes a partir de los documentos encontrados...\n Inciendias encontradas durante la generación de expedientes:\n")
        expedientes = extract_expedientes(documents)
        print(f"\nSe generaron {len(expedientes)} expedientes a partir de los documentos encontrados\n")
        report_path = write_report(output_path, documents, expedientes, inbox_path)
        print("--- PROCESO FINALIZADO ---")
        print(f"Informe generado en: {report_path}")
        print(f"Consulta el informe para ver los archivos que requieren atención,los expedientes incompletos o con duplicados y los archivos renombrados.")
        sys.exit(0)


if __name__ == "__main__":
    """
    Main entry point for the script. It handles command-line arguments and calls the main function.
    """
    # Check for help argument and display usage information if present
    if len(sys.argv) > 1 and sys.argv[1] in ("help", "-h", "--help"):
        print("Uso:")
        print("  python3 src/main.py <ruta_inbox> <ruta_salida>\n")
        print("  - La ruta de entrada debe ser un directorio que contenga los documentos a procesar.\n")
        print("  - Si solo indicas la ruta de inbox, la salida se generará en test_output\n")
        print("Si no indicas rutas:")
        print("  - inbox por defecto: dataset/inbox")
        print("  - salida por defecto: test_output\n")
        print("Para runear el test default, ejecuta: python3 -m tests.run_sorter_default_test\n")
        sys.exit(0)

    # Define default paths for inbox and output
    base_dir = Path(__file__).resolve().parent.parent
    default_inbox_path = base_dir / "dataset" / "inbox"
    default_output_path = base_dir / "test_output"
    
    # Take inbox and output paths from command line arguments or use defaults
    if len(sys.argv) > 2 and sys.argv[1].strip() and sys.argv[2].strip():
        inbox_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1].strip():
        inbox_path = Path(sys.argv[1])
        output_path = default_output_path
    else:
        inbox_path = default_inbox_path
        output_path = default_output_path

    # User confirmation of the paths being used
    print(f"Ruta de entrada: {inbox_path}")
    print(f"Ruta de salida: {output_path}")
    response = input("¿Quieres usar estas rutas? [y/n]: ").strip().lower()
    if not response in ("y", "yes", "s", "si"):
        print("Proceso cancelado por el usuario.")
        sys.exit(0)

    # Check if the inbox path exists and is a directory before proceeding
    if inbox_path.exists() and inbox_path.is_dir():
        main(inbox_path, output_path)
    else:
        print(f"La ruta de entrada no existe o no es un directorio: {inbox_path}")
        print("No se generará un informe de salida.")
        sys.exit(0)