from dataclasses import dataclass

@dataclass
class AsistentZauzeca():
    asistentId: str
    brojTermina: int

    @staticmethod
    def from_json(obj: any) -> 'AsistentZauzeca':
        _asistentId = str(obj.get("asistentId"))
        _brojTermina = int(obj.get("brojTermina"))
        return AsistentZauzeca(_asistentId, _brojTermina)

@dataclass
class PredmetPredavac():
    predmetId: str
    predmetOznaka: str
    predmetGodina: int
    predmetPlan: int
    profesorId: str
    ostaliProfesori: list[str]
    asistentZauzeca: list[AsistentZauzeca]

    @staticmethod
    def from_json(obj: any) -> 'PredmetPredavac':
        _predmetId = str(obj.get("predmetId"))
        _predmetOznaka = str(obj.get("predmetOznaka"))
        _predmetGodina = int(obj.get("predmetGodina"))
        _predmetPlan = int(obj.get("predmetPlan"))
        _profesorId = str(obj.get("profesorId"))
        _ostaliProfesori = [str(y) for y in obj.get("ostaliProfesori")]
        _asistentZauzeca = [AsistentZauzeca.from_json(y) for y in obj.get("asistentZauzeca")]
        return PredmetPredavac(_predmetId, _predmetOznaka, _predmetGodina, _predmetPlan, _profesorId, _ostaliProfesori, _asistentZauzeca)


@dataclass
class StudijskiProgramPredmeti():
    id: str
    studijskiProgramId: str
    predmetPredavaci: list[PredmetPredavac]

    @staticmethod
    def from_json(obj: any) -> 'StudijskiProgramPredmeti':
        _id = str(obj.get("id"))
        _studijskiProgramId = str(obj.get("studijskiProgramId"))
        _predmetPredavaci = [PredmetPredavac.from_json(y) for y in obj.get("predmetPredavaci")]
        return StudijskiProgramPredmeti(_id, _studijskiProgramId, _predmetPredavaci)

@dataclass
class Realizacija():
    godina: str
    semestar: str
    studijskiProgramPredmeti: list[StudijskiProgramPredmeti]

    @staticmethod
    def from_json(obj: any) -> 'Realizacija':
        _godina = str(obj.get("godina"))
        _semestar = str(obj.get("semestar"))
        _studijskiProgrami = [StudijskiProgramPredmeti.from_json(y) for y in obj.get("studijskiProgramPredmeti")]
        return Realizacija(_godina, _semestar, _studijskiProgrami)

# Example Usage
# jsonstring = json.loads(myjsonstring)
# root = Realizacija.from_json(jsonstring)
