from dataclasses import dataclass
import inspect
import json

# utility za pisanje klasa u fajlove
class ClassEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

@dataclass
class ReadWrite:
    @classmethod
    def from_json(cls, data):
        return cls(**{
            k: v for k, v in data.items() 
            if k in inspect.signature(cls).parameters
        })
        # return cls(**data)
    
    @classmethod
    def from_json_list(cls, data):
        return list(map(cls.from_json, data))

    @classmethod
    def write_to_file(
            cls, 
            data, 
            file_name: str,
            dir_path: str = '../out_data/'
    ):
        with open(dir_path + file_name + '.json', 'w', encoding='utf-8') as out_file:
            json_data = json.dumps(data, indent=4, cls=ClassEncoder, ensure_ascii=False)
            out_file.write(json_data)

    @classmethod
    def read_list_from_file(
            cls,
            file_name: str,
            dir_path: str = '../out_data/'
    ):
        with open(dir_path + file_name + '.json', 'r', encoding='utf-8') as in_file:
            data = cls.from_json_list(json.load(in_file))
        return data

    @classmethod
    def read_entity_from_file(
            cls,
            file_name: str,
            dir_path: str = '../out_data/'
    ):
        with open(dir_path + file_name + '.json', 'r', encoding='utf-8') as in_file:
            data = cls.from_json(json.load(in_file))
        return data


@dataclass
class RasporedIds(ReadWrite):
    oznakaKatedre_id: str = None
    predmet_id: str = None
    studProgram_id: str = None
    predavac_id: str = None
    ostaliPredavaci: list[str] = None

# parsiranje rasporeda
@dataclass
class RasporedTermin(RasporedIds):
    sifraStruke: str = None
    semestar: str = None
    predmet: str = None
    tipNastave: str = None
    studGrupa: str = None
    predavac: str = None
    oznakaKatedre: str = None
    ukupnoStud: str = None
    trajanje: int = None

    # parsirana imena svih predavaca u terminu - medjukorak, da li je potreban u modelu???
    predavaci_imena: list[tuple[str]] = None


# parsiranje ulaznih fajlova
@dataclass
class Departman(ReadWrite):
    id: str
    oznaka: str
    ssluzbaOznaka: str
    naziv: str

@dataclass
class Katedra(ReadWrite):
    id: str
    oznaka: str
    ssluzbaOznaka: str
    naziv: str
    departman: str

@dataclass
class Predavac(ReadWrite):
    id: str
    oznaka: int
    ime: str
    prezime: str
    organizacijaFakulteta: bool
    dekanat: bool
    orgJedinica: str
    titula: str = ''

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            getattr(other, 'ime', None) == self.ime and
            getattr(other, 'prezime', None) == self.prezime)

    def __hash__(self):
        return hash(self.ime + self.prezime)

@dataclass
class StudijskiProgram(ReadWrite):
    id: str
    stepen: int
    nivo: int
    oznaka: str
    naziv: str

    def __hash__(self):
        return hash(self.oznaka)
    
@dataclass
class Predmet(ReadWrite):
    id: str
    oznaka: str
    plan: int
    naziv: str
    godina: int
    semestar: str # L/Z
    brojCasovaPred: int
    studijskiProgram: str = ''
    brojCasovaVezbe: int = -1
    # radi spajanja sa rasporedom
    sifraStruke: str = ''
    # nepoznati iz rasporeda
    tipoviNastave: str = ''
    brojCasovaAud: int = -1
    brojCasovaLab: int = -1
    brojCasovaRac: int = -1

    def __hash__(self):
        return hash(self.oznaka)
    
# kako znamo koja grupa slusa koje predmete kada imamo izborne?
@dataclass
class StudentskaGrupa(ReadWrite):
    id: str
    oznaka: int # citamo je iz rasporeda (bitne oznake zbog mapiranja na podsmerove)
    godina: int
    semestar: str # L/Z
    brojStudenata: int
    studijskiProgram: str

    def __hash__(self):
        return hash(self.oznaka)

@dataclass
class Prostorija(ReadWrite):
    id: str
    oznaka: str
    tip: str
    kapacitet: int
    orgJedinica: list[str]
    oznakaSistem: str = None
    sekundarniTip: str = None
    sekundarnaOrgJedinica: list[str] = None
    odobreniPredmeti: list[str] = None

@dataclass
class Dan(ReadWrite):
    id: int
    danUNedelji: int

@dataclass
class TimeGrain(ReadWrite):
    id: str
    grainIndex: int
    pocetniMinut: int
    dan: int
    
# TODO
# GENERISANJE GRUPA DELIMICNO GOTOVO (racunarske spajanje grupa ostalo)
@dataclass
class Meeting(ReadWrite):
    id: str
    # ovo nam je bitno!
    tipProstorije: str
    # ovo nam je za ispis ('Pred.', 'lab.vežbe',...)
    meetingTip: str
    # 1 cas = 45 min
    brojCasova: int
    predavac: str
    ostaliPredavaci: list[str]
    predmet: str
    studentskeGrupe: list[str] # NIZ ID-EVA
    biWeekly: bool = False
    

@dataclass
class MeetingAssignment(ReadWrite):
    id: str
    meeting: Meeting
    startingTimeGrain: TimeGrain = None #-> inicijalno null, postavlja ih sistem
    prostorija: Prostorija = None #-> inicijalno null, postavlja ih sistem

@dataclass
class MeetingSchedule(ReadWrite):
    semestar: str
    departmanList: list[Departman]
    katedraList: list[Katedra]
    predmetList: list[Predmet]
    studProgramList: list[StudijskiProgram]
    prostorijaList: list[Prostorija]
    predavacList: list[Predavac]
    studentskaGrupaList: list[StudentskaGrupa]
    danList: list[Dan]
    timeGrainList: list[TimeGrain]
    meetingList: list[Meeting] = None # lista koju kreiramo tek nakon ucitavanja svih fajlova
    # zbog naknadnog optimizovanja MAS -> nije obavezna
    meetingAssignmentList: list[MeetingAssignment] = None # lista koju dobijemo od optimizatora

    @classmethod
    def from_json(cls, data):
        semestar = str(data['semestar'])
        departmanList = list(map(Departman.from_json, data['departmanList']))
        katedraList = list(map(Katedra.from_json, data['katedraList']))
        predmetList = list(map(Predmet.from_json, data['predmetList']))
        studProgramList = list(map(StudijskiProgram.from_json, data['studProgramList']))
        prostorijaList = list(map(Prostorija.from_json, data['prostorijaList']))
        predavacList = list(map(Predavac.from_json, data['predavacList']))
        studentskaGrupaList = list(map(StudentskaGrupa.from_json, data['studentskaGrupaList']))
        danList = list(map(Dan.from_json, data['danList']))
        timeGrainList = list(map(TimeGrain.from_json, data['timeGrainList']))
        meetingList = None
        if data['meetingList']:
            meetingList = list(map(Meeting.from_json, data['meetingList']))
        meetingAssignmentList = None
        if data['meetingAssignmentList']:
            meetingAssignmentList = list(map(MeetingAssignment.from_json, data['meetingAssignmentList']))
        return cls(semestar, \
            departmanList, katedraList, predmetList, studProgramList, \
            prostorijaList, predavacList, studentskaGrupaList, \
            danList, timeGrainList, \
            meetingList, meetingAssignmentList)


# Kombinovanje vise studijskih programa u jedan Raspored
# Parsiranje iz plana
@dataclass
class RasporedPrikaz(ReadWrite):
    nazivRasporeda: str
    studProgrami: list[str]

    @classmethod
    def from_json(cls, obj: any) -> 'RasporedPrikaz':
        _nazivRasporeda = str(obj.get("nazivRasporeda"))
        _studProgrami = [str(y) for y in obj.get("studProgrami")]
        return cls(_nazivRasporeda, _studProgrami)
