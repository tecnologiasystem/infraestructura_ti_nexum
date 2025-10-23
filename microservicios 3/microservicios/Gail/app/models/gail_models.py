from typing import List, Optional
from pydantic import BaseModel, Field

"""
📦 Modelo que representa un número de teléfono asociado a un contacto.
- `number`: Número telefónico (obligatorio).
- `type`: Tipo del número (ej. móvil, fijo, etc.), es opcional.
"""
class PhoneNumber(BaseModel):
    number: str
    type: Optional[str] = None

"""
📦 Modelo principal de un contacto dentro de una campaña GAIL.
Incluye datos básicos como nombre, teléfono, emails y un campo adicional para otros datos.
- `id`: Identificador único del contacto (UUID).
- `status`: Estado actual del contacto (ej. activo, inactivo).
- `firstName`, `lastName`: Nombre y apellido del contacto.
- `businessName`: Nombre comercial, si aplica.
- `source`: Fuente del contacto (de dónde proviene).
- `phoneNumbers`: Lista de números telefónicos asociados.
- `emails`: Lista de correos electrónicos.
- `additionalData`: Diccionario con datos adicionales (ej. cedula, banco, etc.).
"""
class ContactoGail(BaseModel):
    id: Optional[str]
    status: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    businessName: Optional[str] = None
    source: Optional[str] = None
    phoneNumbers: Optional[List[PhoneNumber]] = []
    emails: Optional[List[str]] = []
    additionalData: Optional[dict] = {}

"""
📦 Modelo de una lista de contactos GAIL.
Se refiere al grupo de contactos asociado a una campaña.
- `id`: Identificador único de la lista.
- `name`: Nombre de la lista de contactos.
- `description`: Descripción opcional de la lista.
"""
class ContactListGail(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

"""
📦 Modelo que representa una secuencia de llamadas o mensajes dentro de una campaña.
- `id`: Identificador de la secuencia.
- `name`: Nombre de la secuencia.
"""
class SequenceGail(BaseModel):
    id: str
    name: str

"""
📦 Modelo que representa la regla de remarcado de la campaña.
- `id`: ID de la regla.
- `name`: Nombre de la regla.
- `outcomes`: Lista de resultados esperados del contacto (ej. ocupado, no contesta, etc.).
- `systemActions`: Diccionario que relaciona cada resultado con acciones automáticas del sistema.
"""
class RedialingRuleGail(BaseModel):
    id: str
    name: str
    outcomes: List[dict] = Field(default_factory=list)
    systemActions: dict = Field(default_factory=dict)

"""
📦 Modelo principal que representa una campaña GAIL completa.
Incluye datos generales y los objetos asociados como lista de contactos, secuencia, regla de remarcado y contactos.
- `idCampana`: ID único de la campaña.
- `name`: Nombre de la campaña.
- `description`: Descripción opcional.
- `status`: Estado actual de la campaña.
- `contactList`: Objeto `ContactListGail` con la lista de contactos.
- `sequence`: Objeto `SequenceGail` con la secuencia a usar.
- `redialingRule`: Objeto `RedialingRuleGail` con la lógica de remarcado.
- `contactos`: Lista de objetos `ContactoGail` asociados a la campaña.
- `pais`: País al que pertenece la campaña.
"""
class CampanaGail(BaseModel):
    idCampana: str
    name: str
    description: Optional[str] = None
    status: str
    contactList: ContactListGail
    sequence: SequenceGail
    redialingRule: RedialingRuleGail
    contactos: List[ContactoGail] = Field(default_factory=list)
    pais: Optional[str] = None
