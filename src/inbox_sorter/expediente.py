from typing import Dict, List


class Expediente:
    # Define the required and optional document types for an expediente
    REQUIRED_TYPES = ("DUA", "FACTURA", "PACKING")
    OPTIONAL_TYPES = ("TRANSPORTE", "CERTORIGEN")

    def __init__(self, mrn: str, cliente: str, nif_cliente: str, mercancia: str, fecha: str) -> None:
        """
        Initialize an Expediente object with the given MRN, CLIENTE, and NIF-CLIENTE.
        """
        self.mrn = mrn
        self.cliente = cliente
        self.nif_cliente = nif_cliente
        self.mercancia = mercancia
        self.fecha = fecha
        self.archivos_por_tipo: Dict[str, List[str]] = {
            "DUA": [],
            "FACTURA": [],
            "PACKING": [],
            "TRANSPORTE": [],
            "CERTORIGEN": [],
        }
        self.archivos_otros_tipos: Dict[str, List[str]] = {}
        self.expediente_is_complete = False
        self.expediente_has_duplicated_types = False

    def add_document(self, tipo: str, mrn: str, nif_cliente: str, cliente: str, mercancia: str, fecha: str, file_name: str) -> None:
        """
        Adds a document to the expediente, ensuring that the MRN, NIF-CLIENTE, and CLIENTE match the expediente's attributes.
        Raises a ValueError if any of the fields do not match.
        """
        # Raise a VlueError if any of the fields do not match the expediente's attributes
        for field_name, field_value in (("mrn", mrn), ("nif_cliente", nif_cliente), ("cliente", cliente), ("mercancia", mercancia), ("fecha", fecha)):
            if field_value != getattr(self, field_name):
                raise ValueError(f"El campo '{field_name.upper()}' del documento '{file_name}' no coincide con el campo correspondiente del expediente.")

        # Add the document to the appropriate list based on its type
        if tipo in self.archivos_por_tipo and mrn == self.mrn and nif_cliente == self.nif_cliente:
            self.archivos_por_tipo[tipo].append(file_name)
            return
        
        if tipo not in self.archivos_por_tipo and mrn == self.mrn and nif_cliente == self.nif_cliente:
            self.archivos_otros_tipos[tipo].append(file_name)
            return

    def missing_required_types(self) -> List[str]:
        """
        Returns a list of required document types that are missing from the expediente.
        """
        missing: List[str] = []
        for required in self.REQUIRED_TYPES:
            if not self.archivos_por_tipo[required]:
                missing.append(required)
        return missing

    def duplicated_types(self) -> List[str]:
        """
        Returns a list of document types that have duplicates in the expediente.
        """
        duplicated: List[str] = []

        for tipo, files in self.archivos_por_tipo.items():
            if len(files) > 1:
                duplicated.append(tipo)

        for tipo, files in self.archivos_otros_tipos.items():
            if len(files) > 1:
                duplicated.append(tipo)

        if len(duplicated) > 0:
            self.expediente_has_duplicated_types = True

        return duplicated

    def is_complete(self) -> bool:
        """
        Checks if the expediente is complete by verifying that all required document types are present.
        """
        self.expediente_is_complete = len(self.missing_required_types()) == 0
        return self.expediente_is_complete
    
    def check_flaws(self) -> None:
        """
        Checks for missing required document types and duplicated document types in the expediente.
        """
        self.is_complete()
        self.duplicated_types()

    def to_dict(self) -> Dict[str, object]:
        """
        Converts the expediente's attributes and document information into a dictionary format.
        """
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