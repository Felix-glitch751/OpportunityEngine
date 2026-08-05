from abc import ABC, abstractmethod

from App.models import Opportunity


class BaseCollector(ABC):
    """
    Clase base para todos los colectores.

    Cualquier fuente (RSS, HTML, API, etc.)
    deberá heredar de esta clase.
    """

    def __init__(
        self,
        source_id: str,
        source_name: str,
        url: str,
        country: str,
        category: str,
    ) -> None:

        self.source_id = source_id
        self.source_name = source_name
        self.url = url
        self.country = country
        self.category = category

    @abstractmethod
    def collect(self) -> list[Opportunity]:
        """
        Debe devolver una lista de objetos Opportunity.
        """

        raise NotImplementedError