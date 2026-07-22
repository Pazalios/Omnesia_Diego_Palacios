from pathlib import Path
from typing import Any, Dict, List, Union
import shutil

from expediente import Expediente

#################################################################################
########### FUNCIONES PARA LEER DOCUMENTOS DE LA CARPETA DE ENTRADA #############
#################################################################################

def read_inbox_documents(inbox_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Reads all the documents in the inbox directory and parses the content of the documents
    """
    inbox_directory = Path(inbox_path)
    documents: List[Dict[str, Any]] = []

    for file_path in inbox_directory.glob("*"):
        if not file_path.is_file() or file_path.suffix.lower() != ".txt":
            documents.append({file_path.name: "Documento no procesable, no es un txt"})
            continue
        else:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                documents.append({file_path.name: "Documento no procesable, error al leer el archivo"})
                continue

            fields = _parse_document_content(content)

            for possible_field in ("MRN", "NIF-CLIENTE", "TIPO", "CLIENTE", "MERCANCIA", "BULTOS", "PESO-KG"):
                if possible_field not in fields:
                    fields["ERRORES"].append(f"En este documento falta el campo {possible_field}")

            if len(fields.get("MRN", "")) < 18:
                fields["ERRORES"].append("En este documento el MRN no tiene el formato correcto, faltan caracteres")
                continue
            elif len(fields.get("MRN", "")) > 18:
                fields["ERRORES"].append("En este documento el MRN no tiene el formato correcto, sobran caracteres")
                continue

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
        if ":" not in raw_line:
            continue

        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key:
            fields[key] = value
    
    # Add an empty list for errors to the fields dictionary
    fields["ERRORES"] = []
    
    # Return the dictionary of fields extracted from the document content
    return fields

#################################################################################
############## FUNCIONES PARA EXTRAER LOS EXPEDIENTES DEL INBOX #################
#################################################################################


def _normalize_document_type(raw_tipo: str) -> str:
    normalized = raw_tipo.strip().upper().replace(" ", "").replace("-", "").replace("_", "")

    if normalized == "DUA":
        return "DUA"
    if normalized == "FACTURA":
        return "FACTURA"
    if normalized in ("PACKING", "PACKINGLIST"):
        return "PACKING"
    if normalized in ("CMR", "TRANSPORTE"):
        return "TRANSPORTE"
    if normalized in ("CERTORIGEN", "CERTIFICADOORIGEN"):
        return "CERTORIGEN"

    return raw_tipo.strip().upper()


def extract_expedientes(documents: List[Dict[str, Any]]) -> List[Expediente]:
    expedientes_by_client: Dict[str, Expediente] = {}

    for document in documents:
        file_name = next(iter(document.keys()))
        payload = document[file_name]

        if not isinstance(payload, dict):
            continue

        mrn = payload.get("MRN")
        tipo = payload.get("TIPO")
        cliente = payload.get("CLIENTE", "SIN_CLIENTE")
        nif_cliente = payload.get("NIF-CLIENTE", "SIN_NIF")

        if not isinstance(mrn, str) or not isinstance(tipo, str):
            continue

        if mrn not in expedientes_by_client:
            expedientes_by_client[mrn] = Expediente(mrn, str(cliente), str(nif_cliente))

        expediente = expedientes_by_client[mrn]

        if expediente.cliente == "SIN_CLIENTE" and isinstance(cliente, str):
            expediente.cliente = cliente

        if expediente.nif_cliente == "SIN_NIF" and isinstance(nif_cliente, str):
            expediente.nif_cliente = nif_cliente

        try:
            expediente.add_document(_normalize_document_type(tipo), mrn, nif_cliente, file_name)
        except ValueError as e:
            print(f"Error al agregar el documento '{file_name}': {e}")            
            document[file_name] = {"Error": f"Documento no procesable, {e}"}

    return sorted(expedientes_by_client.values(), key=lambda expediente: (expediente.cliente, expediente.nif_cliente, expediente.mrn))


def serialize_expedientes(expedientes: List[Expediente]) -> List[Dict[str, object]]:
    return [expediente.to_dict() for expediente in expedientes]

#################################################################################
########### FUNCIONES PARA ESCRIBIR EL INFORME Y ORGANIZAR ARCHIVOS #############
#################################################################################

def write_report(output_path: Path, documents: list, expedientes: list, inbox_path: Path) -> Path:
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "otros_archivos").mkdir(parents=True, exist_ok=True)

    report_lines = ["INFORME DE EXPEDIENTES", ""]
    report_lines.append(f"Total documentos leidos: {len(documents)}")
    report_lines.append(f"Total expedientes: {len(expedientes)}")
    report_lines.append("")

    invalid_documents = []
    for document in documents:
        file_name = next(iter(document.keys()))
        payload = document[file_name]

        if not isinstance(payload, dict):
            invalid_documents.append((file_name, payload))
            _copy_document(inbox_path, output_path / "otros_archivos", file_name)

    for expediente in expedientes:
        client_folder_name = _safe_folder_name(f"{expediente.cliente}-{expediente.nif_cliente}")
        expediente_folder = output_path / client_folder_name / _safe_folder_name(expediente.mrn)
        expediente_folder.mkdir(parents=True, exist_ok=True)

        for files in expediente.archivos_por_tipo.values():
            for file_name in files:
                _copy_document(inbox_path, expediente_folder, file_name)

        for files in expediente.archivos_otros_tipos.values():
            for file_name in files:
                _copy_document(inbox_path, expediente_folder, file_name)

        report_lines.append(f"MRN: {expediente.mrn}")
        report_lines.append(f"CLIENTE: {expediente.cliente}")
        report_lines.append(f"NIF-CLIENTE: {expediente.nif_cliente}")
        report_lines.append(f"ESTADO: {'COMPLETO' if expediente.is_complete() else 'INCOMPLETO'}")
        report_lines.append(f"FALTAN: {', '.join(expediente.missing_required_types()) if expediente.missing_required_types() else 'NINGUNO'}")
        report_lines.append(f"DUPLICADOS: {', '.join(expediente.duplicated_types()) if expediente.duplicated_types() else 'NINGUNO'}")
        report_lines.append("ARCHIVOS:")
        for tipo, files in expediente.archivos_por_tipo.items():
            report_lines.append(f"  - {tipo}: {', '.join(files) if files else '---'}")
        if expediente.archivos_otros_tipos:
            report_lines.append("  - OTROS TIPOS:")
            for tipo, files in expediente.archivos_otros_tipos.items():
                report_lines.append(f"    * {tipo}: {', '.join(files)}")
        report_lines.append("")

    if invalid_documents:
        report_lines.append("ARCHIVOS SIN MRN")
        for file_name, reason in invalid_documents:
            report_lines.append(f"- {file_name}: {reason}")
        report_lines.append("")

    report_path = output_path / "Informe_generado.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return report_path


def _copy_document(inbox_path: Path, output_folder: Path, file_name: str) -> None:
    source_file = inbox_path / file_name
    if source_file.exists():
        shutil.copy2(source_file, output_folder / file_name)


def _safe_folder_name(value: str) -> str:
    cleaned = value.strip()
    for character in ("/", "\\", ":", "*", "?", '"', "<", ">", "|"):
        cleaned = cleaned.replace(character, "_")
    cleaned = cleaned.replace("  ", " ")
    return cleaned or "SIN_NOMBRE"