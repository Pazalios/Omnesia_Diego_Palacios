from typing import Dict, List


class Expediente:
    REQUIRED_TYPES = ("DUA", "FACTURA", "PACKING")
    OPTIONAL_TYPES = ("TRANSPORTE", "CERTORIGEN")

    def __init__(self, mrn: str, cliente: str, nif_cliente: str) -> None:
        self.mrn = mrn
        self.cliente = cliente
        self.nif_cliente = nif_cliente
        self.archivos_por_tipo: Dict[str, List[str]] = {
            "DUA": [],
            "FACTURA": [],
            "PACKING": [],
            "TRANSPORTE": [],
            "CERTORIGEN": [],
        }
        self.archivos_otros_tipos: Dict[str, List[str]] = {}

    def add_document(self, tipo: str, mrn: str, nif_cliente: str, file_name: str) -> None:
        if tipo in self.archivos_por_tipo and mrn == self.mrn and nif_cliente == self.nif_cliente:
            self.archivos_por_tipo[tipo].append(file_name)
            return

        if tipo not in self.archivos_por_tipo and mrn == self.mrn and nif_cliente == self.nif_cliente:
            self.archivos_otros_tipos[tipo].append(file_name)
            return
        
        if nif_cliente != self.nif_cliente:
            raise ValueError(f"El NIF-CLIENTE, {nif_cliente}, del documento '{file_name}' no coincide con el NIF-CLIENTE del expediente '{self.nif_cliente}'.")

    def missing_required_types(self) -> List[str]:
        missing: List[str] = []
        for required in self.REQUIRED_TYPES:
            if not self.archivos_por_tipo[required]:
                missing.append(required)
        return missing

    def duplicated_types(self) -> List[str]:
        duplicated: List[str] = []

        for tipo, files in self.archivos_por_tipo.items():
            if len(files) > 1:
                duplicated.append(tipo)

        for tipo, files in self.archivos_otros_tipos.items():
            if len(files) > 1:
                duplicated.append(tipo)

        return sorted(duplicated)

    def is_complete(self) -> bool:
        return len(self.missing_required_types()) == 0

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "MRN": self.mrn,
            "CLIENTE": self.cliente,
            "NIF-CLIENTE": self.nif_cliente,
            "archivos": self.archivos_por_tipo,
            "estado": "completo" if self.is_complete() else "incompleto",
            "faltan": self.missing_required_types(),
            "archivos_duplicados": self.duplicated_types(),
        }

        if self.archivos_otros_tipos:
            data["archivos_otros_tipos"] = self.archivos_otros_tipos

        return data