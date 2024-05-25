from dataclasses import dataclass

# Kombinovanje vise studijskih programa u jedan Raspored
# Parsiranje iz plana
@dataclass
class RasporedPrikaz():
    nazivRasporeda: str
    studProgrami: list[str]

    @classmethod
    def from_json(cls, obj: any) -> 'RasporedPrikaz':
        _nazivRasporeda = str(obj.get("nazivRasporeda"))
        _studProgrami = [str(y) for y in obj.get("studProgrami")]
        return cls(_nazivRasporeda, _studProgrami)
