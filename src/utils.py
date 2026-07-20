from pathlib import Path
from typing import Any, Dict, List, Union

from expediente import Expediente


def _parse_document_content(content: str) -> Dict[str, str]:
    """
    Parsea el contenido de un documento y devuelve un diccionario con los campos encontrados.
    """
    fields: Dict[str, str] = {}

    for raw_line in content.splitlines():
        if ":" not in raw_line:
            continue

        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key:
            fields[key] = value

    return fields


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


def read_inbox_documents(inbox_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Lee todos los documentos de texto en el directorio de entrada y devuelve una lista de diccionarios
    """
    inbox_directory = Path(inbox_path)
    documents: List[Dict[str, Any]] = []

    for file_path in inbox_directory.glob("*.txt"):
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            documents.append({file_path.name: "documento no procesable, no es un txt"})
            continue

        fields = _parse_document_content(content)

        if "MRN" not in fields:
            documents.append({file_path.name: "documento no procesable, falta MRN"})
            continue

        if "NIF-CLIENTE" not in fields:
            documents.append({file_path.name: "documento no procesable, falta NIF-CLIENTE"})
            continue

        if "TIPO" not in fields:
            documents.append({file_path.name: "documento no procesable, falta TIPO"})
            continue

        documents.append({file_path.name: fields})

    return documents


def extract_expedientes(documents: List[Dict[str, Any]]) -> List[Expediente]:
    expedientes_by_mrn: Dict[str, Expediente] = {}

    for document in documents:
        file_name = next(iter(document.keys()))
        payload = document[file_name]

        if not isinstance(payload, dict):
            continue

        mrn = payload.get("MRN")
        tipo = payload.get("TIPO")

        if not isinstance(mrn, str) or not isinstance(tipo, str):
            continue

        if mrn not in expedientes_by_mrn:
            expedientes_by_mrn[mrn] = Expediente(mrn)

        expedientes_by_mrn[mrn].add_document(_normalize_document_type(tipo), file_name)

    return sorted(expedientes_by_mrn.values(), key=lambda expediente: expediente.mrn)


def serialize_expedientes(expedientes: List[Expediente]) -> List[Dict[str, object]]:
    return [expediente.to_dict() for expediente in expedientes]