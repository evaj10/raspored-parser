from dataclasses import dataclass

# parsiranje ulaznih fajlova
@dataclass
class OrganizacionaJedinica():
    id: str
    oznaka: str
    ssluzbaOznaka: str
    naziv: str

@dataclass
class Departman(OrganizacionaJedinica):
    pass

@dataclass
class Katedra(OrganizacionaJedinica):
    departman: Departman

@dataclass
class Predavac():
    id: str
    oznaka: int
    ime: str
    prezime: str
    organizacijaFakulteta: bool
    dekanat: bool
    orgJedinica: OrganizacionaJedinica
    titula: str = ''

@dataclass
class StudijskiProgram():
    id: str
    stepen: int
    nivo: int
    oznaka: str
    naziv: str
    
@dataclass
class Predmet():
    id: str
    oznaka: str
    plan: int
    naziv: str
    godina: int
    semestar: str # L/Z
    brojCasovaPred: int
    studijskiProgram: StudijskiProgram
    brojCasovaVezbe: int = -1
    # radi spajanja sa rasporedom
    sifraStruke: str = ''
    # nepoznati iz rasporeda
    tipoviNastave: str = ''
    brojCasovaAud: int = -1
    brojCasovaLab: int = -1
    brojCasovaRac: int = -1
    
@dataclass
class StudentskaGrupa():
    id: str
    oznaka: int # citamo je iz rasporeda (bitne oznake zbog mapiranja na podsmerove)
    godina: int
    semestar: str # L/Z
    brojStudenata: int
    studijskiProgram: StudijskiProgram

@dataclass
class Prostorija():
    id: str
    oznaka: str
    tip: str
    kapacitet: int
    orgJedinica: OrganizacionaJedinica
    oznakaSistem: str = None
    sekundarniTip: str = None
    sekundarnaOrgJedinica: OrganizacionaJedinica
    odobreniPredmeti: Predmet

@dataclass
class Dan():
    id: int
    danUNedelji: int

@dataclass
class TimeGrain():
    id: str
    grainIndex: int
    pocetniMinut: int
    dan: Dan
    
@dataclass
class Meeting():
    id: str
    tipProstorije: str
    meetingTip: str
    brojCasova: int
    predavac: Predavac
    ostaliPredavaci: Predavac
    predmet: Predmet
    studentskeGrupe: StudentskaGrupa
    biWeekly: bool = False
    

@dataclass
class MeetingAssignment():
    id: str
    meeting: Meeting
    startingTimeGrain: TimeGrain = None #-> inicijalno null, postavlja ih sistem
    prostorija: Prostorija = None #-> inicijalno null, postavlja ih sistem

@dataclass
class MeetingSchedule():
    semestar: str
    departmanList: Departman
    katedraList: Katedra
    predmetList: Predmet
    studProgramList: StudijskiProgram
    prostorijaList: Prostorija
    predavacList: Predavac
    studentskaGrupaList: StudentskaGrupa
    danList: Dan
    timeGrainList: TimeGrain
    meetingList: Meeting = None # Lista koju kreiramo tek nakon ucitavanja svih fajlova
    # zbog naknadnog optimizovanja MAS -> nije obavezna
    meetingAssignmentList: MeetingAssignment = None # Lista koju dobijemo od optimizatora
