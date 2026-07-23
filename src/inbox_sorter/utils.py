from pathlib import Path
from typing import Any, Dict, List, Union
import shutil
import re

from .expediente import Expediente

#################################################################################
########### FUNCIONES PARA LEER DOCUMENTOS DE LA CARPETA DE ENTRADA #############
#################################################################################

def read_inbox_documents(inbox_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Reads all the documents in the inbox directory and parses the content of the documents
    """
    inbox_directory = Path(inbox_path)
    documents: List[Dict[str, Any]] = []

    # Iterate through all files in the inbox directory
    for file_path in inbox_directory.glob("*"):
        
        # Check if the file is a regular file and has a .txt extension
        if not file_path.is_file() or file_path.suffix.lower() != ".txt":
            
            # Add a message to the documents list indicating that the file is not processable
            print(f"    El archivo '{file_path.name}' no es un documento procesable, no es un txt")
            documents.append({file_path.name: "Documento no procesable, no es un txt"})
            continue
        
        else:
            # Try to read the content of the file, handling any errors that may occur
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                print(f"    Error al leer el archivo '{file_path.name}'")
                documents.append({file_path.name: "Documento no procesable, error al leer el archivo"})
                continue
            
            # Parse the content of the document to extract fields
            fields = _parse_document_content(content)

            # If the MRN field is missing, add an error message to the fields dictionary
            if "MRN" not in fields:
                print(f"    En el documento '{file_path.name}' falta el campo MRN")
                fields["ERRORES"].append(f"En este documento falta el campo MRN")
            
            # Else, if the MRN field is present, check for missing fields and validate the MRN format
            else:
                # Check for missing required fields and add error messages to the fields dictionary
                for possible_field in ("NIF-CLIENTE", "TIPO", "CLIENTE", "FECHA", "MERCANCIA", "BULTOS", "PESO-KG"):
                    if possible_field not in fields:
                        print(f"    En el documento '{file_path.name}' falta el campo {possible_field}")
                        fields["ERRORES"].append(f"En este documento falta el campo {possible_field}")

                # Validate the MRN field to ensure it has the correct format and characters)
                if len(fields.get("MRN", "")) < 18:
                    print(f"    El MRN del documento '{file_path.name}' no tiene el formato correcto, faltan caracteres")
                    fields["ERRORES"].append("En este documento el MRN no tiene el formato correcto, faltan caracteres")
                elif len(fields.get("MRN", "")) > 18:
                    print(f"    El MRN del documento '{file_path.name}' no tiene el formato correcto, sobran caracteres")
                    fields["ERRORES"].append("En este documento el MRN no tiene el formato correcto, sobran caracteres")
                elif not re.match(r"^[A-Z0-9]{18}$", fields.get("MRN", "")):
                    print(f"    El MRN del documento '{file_path.name}' no tiene el formato correcto, no cumple con el patrón esperado")
                    fields["ERRORES"].append("En este documento el MRN no tiene el formato correcto, no cumple con el patrón esperado")
                
                # Validate the name of the document to ensure it matches the TIPO, MRN, FECHA and NIF-CLIENTE fields
                file_name_parts = re.split("[ _]+", file_path.stem)
                try:
                    for field_value, file_part in zip((fields.get("TIPO", ""), fields.get("MRN", ""), fields.get("FECHA", "").replace("-", ""), fields.get("NIF-CLIENTE", "")), file_name_parts[0:3]):
                        if field_value and field_value != file_part:
                            print(f"    El nombre del documento '{file_path.name}' no está correcto, se esperaba {field_value} y se encontró {file_part}, se cambiará el nombre del documento")
                            fields["rename_to"] = f"{fields.get('TIPO', '')}_{fields.get('MRN', '')}_{fields.get('FECHA', '').replace('-', '')}_{fields.get('NIF-CLIENTE', '')}.txt"
                except IndexError:
                    print(f"    El nombre del documento '{file_path.name}' no tiene el formato correcto, posiblemente es un archivo duplicado")
                    fields["ERRORES"].append("El nombre del documento no tiene el formato correcto, seguramente es un archivo duplicado")

            # Add the document's file name and its parsed fields to the documents list
            documents.append({file_path.name: fields})
            
    return documents


def _parse_document_content(content: str) -> Dict[str, str]:
    """
    Parses the content of a document and returns a dictionary of fields.
    Each line in the content should be in the format "KEY: VALUE".
    """
    fields: Dict[str, str] = {}
    
    # Iterate through each line in the content and extract key-value pairs
    for raw_line in content.splitlines():
        
        # If the line does not contain a colon, skip it
        if ":" not in raw_line:
            continue
        
        # Split the line into key and value at the first colon and strip whitespace
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()

        # Add the key-value pair to the fields dictionary if the key is not empty
        if key:
            fields[key] = value
    
    # Add an empty list for errors to the fields dictionary
    fields["ERRORES"] = []

    # Add a rename_to field to the fields dictionary
    fields["rename_to"] = ""
    
    # Return the dictionary of fields extracted from the document content
    return fields


#################################################################################
############## FUNCIONES PARA EXTRAER LOS EXPEDIENTES DEL INBOX #################
#################################################################################


def extract_expedientes(documents: List[Dict[str, Any]]) -> List[Expediente]:
    """
    Extracts expedientes from the list of documents and returns a sorted list of Expediente objects.
    """

    expedientes_by_client: Dict[str, Expediente] = {}

    # Iterate through each document in the list of documents
    for document in documents:
        file_name = next(iter(document.keys()))
        payload = document[file_name]

        # Check if the payload is a dictionary, if not, skip to the next document
        if not isinstance(payload, dict):
            continue

        # Extract the MRN, TIPO, CLIENTE, NIF-CLIENTE, MERCANCIA and FECHA fields from the payload
        mrn = payload.get("MRN")
        tipo = payload.get("TIPO")
        cliente = payload.get("CLIENTE")
        nif_cliente = payload.get("NIF-CLIENTE")
        mercancia = payload.get("MERCANCIA")
        fecha = payload.get("FECHA")
        #bultos = payload.get("BULTOS")
        #peso_kg = payload.get("PESO-KG")

        # Check if the MRN and TIPO fields are strings, if not or if there are errors, skip to the next document
        if not isinstance(mrn, str) or not isinstance(tipo, str) or payload.get("ERRORES") != []:
            continue

        # If the MRN is not already in the expedientes_by_client dictionary, create a new Expediente object and add it to the dictionary
        if mrn not in expedientes_by_client:
            #Create a new Expediente object for the MRN and add it to the expedientes_by_client dictionary
            expedientes_by_client[mrn] = Expediente(mrn, cliente, nif_cliente, mercancia, fecha)
            expediente = expedientes_by_client[mrn]
            # Add the document to the new Expediente object
            expediente.add_document(tipo, mrn, nif_cliente, cliente, mercancia, fecha, file_name)
        # If the MRN is already in the expedientes_by_client dictionary, retrieve the existing Expediente object
        else:
            # Open the existing Expediente object for the MRN
            expediente = expedientes_by_client[mrn]

            # Add the document to the Expediente object, handling any errors that may occur
            try:
                expediente.add_document(tipo, mrn, nif_cliente, cliente, mercancia, fecha, file_name)
            except ValueError as e:
                print(f"    Error al agregar el documento '{file_name}': {e}")            
                document[file_name]["ERRORES"] = [str(e)]

    # Check for flaws in each Expediente object and update their status
    for expediente in expedientes_by_client.values():
        expediente.check_flaws()

    # Return a sorted list of Expediente objects based on CLIENTE, NIF-CLIENTE, and MRN
    return sorted(expedientes_by_client.values(), key=lambda expediente: (expediente.cliente, expediente.nif_cliente, expediente.mrn))


def serialize_expedientes(expedientes: List[Expediente]) -> List[Dict[str, object]]:
    """
    Serializes a list of Expediente objects into a list of dictionaries.
    """
    return [expediente.to_dict() for expediente in expedientes]

#################################################################################
########### FUNCIONES PARA ESCRIBIR EL INFORME Y ORGANIZAR ARCHIVOS #############
#################################################################################

def write_report(output_path: Path, documents: list, expedientes: list, inbox_path: Path) -> Path:
    """
    Writes a report of the expedientes and organizes the documents into folders based on their status.
    """

    # Create the output directory and subdirectories for organizing files
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "otros_archivos").mkdir(parents=True, exist_ok=True)
    (output_path / "expedientes_completos").mkdir(parents=True, exist_ok=True)
    (output_path / "expedientes_incompletos").mkdir(parents=True, exist_ok=True)
    (output_path / "archivos_que_requieren_atencion").mkdir(parents=True, exist_ok=True)

    # Generate the report lines with summary information about the documents and expedientes
    report_lines = ["INFORME DE EXPEDIENTES", ""]
    report_lines.append(f"Total documentos leidos: {len(documents)}")
    report_lines.append(f"Total expedientes completos: {len([exp for exp in expedientes if exp.expediente_is_complete])}")
    report_lines.append(f"Total expedientes incompletos: {len([exp for exp in expedientes if not exp.expediente_is_complete])}\n")
    report_lines.append("\nExpdientes completos:\n")

    # Write the report and organize for expedientes that are complete
    for expediente in expedientes:
        if expediente.expediente_is_complete:
            # Create a folder for the expediente in the "expedientes_completos" directory
            client_folder_name = _safe_folder_name(f"{expediente.cliente}-{expediente.nif_cliente}")
            expediente_folder = output_path / "expedientes_completos" / client_folder_name / _safe_folder_name(expediente.mrn)
            expediente_folder.mkdir(parents=True, exist_ok=True)

            copied_files = []

            # Copy the documents associated with the expediente to the corresponding folder
            for files in expediente.archivos_por_tipo.values():
                for file_name in files:
                    _copy_document(inbox_path, expediente_folder, file_name)
                    copied_files.append(file_name)

            for files in expediente.archivos_otros_tipos.values():
                for file_name in files:
                    _copy_document(inbox_path, expediente_folder, file_name)
                    copied_files.append(file_name)

            # Rename copied files if they have a rename_to value in documents.
            for file_name in copied_files:
                _rename_document_if_needed(documents, expediente_folder, file_name)

            # Move duplicated files into a folder inside the expediente.
            _move_duplicated_documents(expediente, expediente_folder, documents)

            # Write the expediente details to the report
            report_lines.append(f"  MRN: {expediente.mrn}")
            report_lines.append(f"  CLIENTE: {expediente.cliente}")
            report_lines.append(f"  NIF-CLIENTE: {expediente.nif_cliente}")
            report_lines.append(f"  ESTADO: {'COMPLETO' if expediente.is_complete() else 'INCOMPLETO'}")
            report_lines.append(f"  DUPLICADOS: {', '.join(expediente.duplicated_types()) if expediente.duplicated_types() else 'NINGUNO'}")
            report_lines.append("  ARCHIVOS:")
            for tipo, files in expediente.archivos_por_tipo.items():
                report_lines.append(f"    - {tipo}: {', '.join(files) if files else '---'}")
            if expediente.archivos_otros_tipos:
                report_lines.append("    - OTROS TIPOS:")
                for tipo, files in expediente.archivos_otros_tipos.items():
                    report_lines.append(f"      * {tipo}: {', '.join(files)}")
            report_lines.append("")
    
    report_lines.append("\nExpdientes incompletos:\n")

    # Write the report and organize for expedientes that are incomplete
    for expediente in expedientes:
        if not expediente.expediente_is_complete:
            # Create a folder for the expediente in the "expedientes_incompletos" directory
            client_folder_name = _safe_folder_name(f"{expediente.cliente}-{expediente.nif_cliente}")
            expediente_folder = output_path / "expedientes_incompletos" / client_folder_name / _safe_folder_name(expediente.mrn)
            expediente_folder.mkdir(parents=True, exist_ok=True)

            copied_files = []

            # Copy the documents associated with the expediente to the corresponding folder
            for files in expediente.archivos_por_tipo.values():
                for file_name in files:
                    _copy_document(inbox_path, expediente_folder, file_name)
                    copied_files.append(file_name)

            for files in expediente.archivos_otros_tipos.values():
                for file_name in files:
                    _copy_document(inbox_path, expediente_folder, file_name)
                    copied_files.append(file_name)

            # Rename copied files if they have a rename_to value in documents.
            for file_name in copied_files:
                _rename_document_if_needed(documents, expediente_folder, file_name)

            # Move duplicated files into a folder inside the expediente.
            _move_duplicated_documents(expediente, expediente_folder, documents)

            # Write the expediente details to the report
            report_lines.append(f"  MRN: {expediente.mrn}")
            report_lines.append(f"  CLIENTE: {expediente.cliente}")
            report_lines.append(f"  NIF-CLIENTE: {expediente.nif_cliente}")
            report_lines.append(f"  ESTADO: {'COMPLETO' if expediente.is_complete() else 'INCOMPLETO'}")
            report_lines.append(f"  FALTAN: {', '.join(expediente.missing_required_types()) if expediente.missing_required_types() else 'NINGUNO'}")
            report_lines.append(f"  DUPLICADOS: {', '.join(expediente.duplicated_types()) if expediente.duplicated_types() else 'NINGUNO'}")
            report_lines.append("  ARCHIVOS:")
            for tipo, files in expediente.archivos_por_tipo.items():
                report_lines.append(f"    - {tipo}: {', '.join(files) if files else '---'}")
            if expediente.archivos_otros_tipos:
                report_lines.append("    - OTROS TIPOS:")
                for tipo, files in expediente.archivos_otros_tipos.items():
                    report_lines.append(f"      * {tipo}: {', '.join(files)}")
            report_lines.append("")

    report_lines.append(f"REVISAR LAS CARPETAS DE DUPLICADOS:")

    # Write the report for expedientes that have duplicated document types
    for expediente in expedientes:
        if expediente.expediente_has_duplicated_types:
            report_lines.append(f"Expediente con duplicados: MRN {expediente.mrn}, CLIENTE {expediente.cliente}, NIF-CLIENTE {expediente.nif_cliente}, Estado: {'COMPLETO' if expediente.is_complete() else 'INCOMPLETO'}")
            report_lines.append(f"  Tipos duplicados: {', '.join(expediente.duplicated_types())}")
            report_lines.append("")

    invalid_documents = []
    must_be_reviewed_documents = []
    renamed_documents = []
    
    # Write the report for documents that are invalid or require attention
    for document in documents:
        file_name = next(iter(document.keys()))
        payload = document[file_name]

        if not isinstance(payload, dict):
            invalid_documents.append((file_name, payload))
            _copy_document(inbox_path, output_path / "otros_archivos", file_name)
        
        if isinstance(payload, dict) and payload.get("ERRORES"):
            if payload.get("ERRORES") != ["En este documento falta el campo MRN"]:
                must_be_reviewed_documents.append((file_name, "; ".join(payload["ERRORES"])))
                _copy_document(inbox_path, output_path / "archivos_que_requieren_atencion", file_name)
            else:
                invalid_documents.append((file_name, "; ".join(payload["ERRORES"])))
                _copy_document(inbox_path, output_path / "otros_archivos", file_name)

        if isinstance(payload, dict) and payload.get("rename_to"):
            renamed_documents.append((file_name, payload["rename_to"]))
    
    # Write the report for documents that are invalid or require attention
    if must_be_reviewed_documents:
        report_lines.append("ARCHIVOS QUE REQUIEREN ATENCION:")
        for file_name, reason in must_be_reviewed_documents:
            report_lines.append(f"- {file_name}: {reason}")
        report_lines.append("")

    # Write the report for documents that have been renamed
    if renamed_documents:
        report_lines.append("ARCHIVOS RENOMBRADOS:")
        for original_name, new_name in renamed_documents:
            report_lines.append(f"- {original_name} -> {new_name}")
        report_lines.append("")

    # Write the report for documents that are invalid
    if invalid_documents:
        report_lines.append("ARCHIVOS SIN MRN:")
        for file_name, reason in invalid_documents:
            report_lines.append(f"- {file_name}: {reason}")
        report_lines.append("")

    # Write the report to a text file in the output directory
    report_path = output_path / "Informe_generado.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return report_path


def _copy_document(inbox_path: Path, output_folder: Path, file_name: str) -> None:
    """
    Copies a document from the inbox directory to the specified output folder.
    """
    source_file = inbox_path / file_name
    if source_file.exists():
        shutil.copy2(source_file, output_folder / file_name)


def _rename_document_if_needed(documents: list, expediente_folder: Path, file_name: str) -> None:
    """
    Renames a document in the expediente folder if it has a rename_to value in the documents list.
    """
    document_payload = _get_document_payload(documents, file_name)

    if isinstance(document_payload, dict):
        rename_to = document_payload.get("rename_to")
        if rename_to:
            original_file = expediente_folder / file_name
            renamed_file = expediente_folder / rename_to
            if original_file.exists():
                original_file.rename(renamed_file)


def _move_duplicated_documents(expediente: Expediente, expediente_folder: Path, documents: list) -> None:
    """
    Moves duplicated documents in the expediente folder to a subfolder named "archivos_duplicados".
    """
    duplicated_types = set(expediente.duplicated_types())

    if not duplicated_types:
        return

    duplicated_folder = expediente_folder / "archivos_duplicados"
    duplicated_folder.mkdir(parents=True, exist_ok=True)

    for tipo in duplicated_types:
        for file_name in expediente.archivos_por_tipo.get(tipo, []):
            _move_document_if_needed(documents, expediente_folder, duplicated_folder, file_name)

        for file_name in expediente.archivos_otros_tipos.get(tipo, []):
            _move_document_if_needed(documents, expediente_folder, duplicated_folder, file_name)


def _move_document_if_needed(documents: list, source_folder: Path, target_folder: Path, file_name: str) -> None:
    """
    Moves a document from the source folder to the target folder if it has a rename_to value in the documents list.
    """
    current_name = _get_document_destination_name(documents, file_name)
    source_file = source_folder / current_name
    target_file = target_folder / current_name

    if source_file.exists():
        source_file.rename(target_file)


def _get_document_payload(documents: list, file_name: str):
    """
    Returns the payload of a document based on its file name from the documents list.
    """
    return next((document[file_name] for document in documents if file_name in document), None)


def _get_document_destination_name(documents: list, file_name: str) -> str:
    """
    Returns the destination name of a document based on its payload in the documents list.
    If the document has a "rename_to" value, it returns that value; otherwise, it returns the original file name.
    """

    document_payload = _get_document_payload(documents, file_name)

    if isinstance(document_payload, dict):
        rename_to = document_payload.get("rename_to")
        if rename_to:
            return rename_to

    return file_name


def _safe_folder_name(value: str) -> str:
    """
    Cleans a string to be used as a safe folder name by removing or replacing invalid characters.
    """
    cleaned = value.strip()
    for character in ("/", "\\", ":", "*", "?", '"', "<", ">", "|"):
        cleaned = cleaned.replace(character, "_")
    cleaned = cleaned.replace("  ", " ")
    return cleaned or "SIN_NOMBRE"