from dataclasses import dataclass
from model_parser import *

@dataclass
class ProstorijaZauzece:
    prostorijaOznaka: str
    firstTimeGrainIndex: int
    lastTimeGrainIndex: int

# posebna klasa koja odgovara DTO optimizatora potrebna za formatiranje rasporeda
@dataclass
class TimeGrainJoined(ReadWrite):
    id: str
    grainIndex: int
    pocetniMinut: int
    dan: Dan

    @classmethod
    def from_json(cls, data):
        if data is None:
            return None
        id = str(data['id'])
        grainIndex = int(data['grainIndex'])
        pocetniMinut = int(data['pocetniMinut'])
        dan = Dan.from_json(data['dan'])
        return cls(id, grainIndex, pocetniMinut, dan)

@dataclass
class StudentskaGrupaJoined(ReadWrite):
    id: str
    oznaka: str
    godina: int
    semestar: str
    brojStudenata: int
    studijskiProgram: StudijskiProgram

    @classmethod
    def from_json(cls, data):
        id = str(data['id'])
        oznaka = str(data['oznaka'])
        godina = int(data['godina'])
        semestar = str(data['semestar'])
        brojStudenata = int(data['brojStudenata'])
        studijskiProgram = StudijskiProgram.from_json(data['studijskiProgram'])
        return cls(id, oznaka, godina, semestar, brojStudenata, studijskiProgram)

@dataclass
class MeetingJoined(ReadWrite):
    id: str
    tipProstorije: str
    meetingTip: str
    predavac: Predavac
    ostaliPredavaci: list[Predavac]
    predmet: Predmet
    brojCasova: int
    durationInGrains: int
    studentskeGrupe: list[StudentskaGrupaJoined]
    requiredCapacity: int
    biWeekly: bool = False

    @classmethod
    def from_json(cls, data):
        id = str(data['id'])
        tipProstorije = str(data['tipProstorije'])
        meetingTip = str(data['meetingTip'])
        predavac = Predavac.from_json(data['predavac'])
        ostaliPredavaci = list(map(Predavac.from_json, data['ostaliPredavaci']))
        predmet = Predmet.from_json(data['predmet'])
        brojCasova = int(data['brojCasova'])
        durationInGrains = int(data['durationInGrains'])
        studentskeGrupe = list(map(StudentskaGrupaJoined.from_json, data['studentskeGrupe']))
        requiredCapacity = int(data['requiredCapacity'])
        biWeekly = bool(data['biWeekly'])
        return cls(id, tipProstorije, meetingTip, predavac, ostaliPredavaci, predmet, \
                   brojCasova, durationInGrains, studentskeGrupe, requiredCapacity, biWeekly)

@dataclass
class MeetingAssignmentJoined(ReadWrite):
    id: str
    meeting: MeetingJoined
    startingTimeGrain: TimeGrainJoined = None
    prostorija: Prostorija = None

    @classmethod
    def from_json(cls, data):
        id = str(data['id'])
        meeting = MeetingJoined.from_json(data['meeting'])
        startingTimeGrain = TimeGrainJoined.from_json(data['startingTimeGrain'])
        prostorija = Prostorija.from_json(data['prostorija'])
        return cls(id, meeting, startingTimeGrain, prostorija)
