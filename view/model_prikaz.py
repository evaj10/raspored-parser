# Raspored:

# Grupa-e	Od	Do	Učionica	Vrsta nast.	Naziv predmeta	Izvođač
# SVI	18:00	19:45	310	Pred.	Tehnička eksploatacija mašina	Dorić dr Jovan

# Prostorije:

# Grupa-e	Od	Do	Odsek	Sem.	Vrsta nast.	Naziv Predmeta	Izvođač
# SVI	7:15	9:00	Struka GI	VI	Pred.	Tehnike štampe	Kašiković dr Nemanja

# Predavaci:

# Grupa-e	Od	Do	Učionica	Odsek	Sem.	Vrsta nast.	Naziv Predmeta
# SVI	13:15	16:00	NTP-A	Struka EET_ME	IV	Pred.	Objektno orijentisano programiranje

# Net Liste:
# Ucionica Dan Od Do Stepen Nivo Oznaka Godina NP Šifra predmeta Naziv predmeta Vrsta nastave Oznaka grupe Izvođač Šifra izvođača
# 00;00;502	1 07:30 09:00 1 1 F10 1 20 RG017 Osnove crtanja za animaciju i vizuelne efekte A 1,3(1-8) Varga Marija 2579


from dataclasses import dataclass
from dataclasses import asdict

from model_parser import ReadWrite

@dataclass
class Red(ReadWrite):
    studGrupa: str
    vremePocetka: str
    vremeKraja: str
    vrstaNastave: str
    nazivPred: str

    @classmethod
    def from_instance(cls, instance):
        return cls(**asdict(instance))

@dataclass
class RasporedRed(Red):
    prostorija: str
    predavac: str

@dataclass
class ProstorijaRed(Red):
    odsek: str
    semestar: str
    predavac: str

@dataclass
class PredavacRed(Red):
    prostorija: str
    odsek: str # naziv smera ce pisati (dugacak)
    semestar: str


# Ucionica Dan  Stepen Nivo Oznaka Godina NP Šifra predmeta  Izvođač Šifra izvođača
# 00;00;502	1  1 1 F10 1 20 RG017  Varga Marija 2579
@dataclass
class NetListaRed(Red):
    prostorija: str
    dan: int
    stepen: int
    nivo: int
    oznaka: str
    godina: int
    plan: int
    predmetOznaka: str
    predavac: str
    predavacOznaka: int

# Red                             = Meeting
# list(Red)                       = RasporedDan
# list(RasporedDan)               = Semestar
# list(Semestar)                  = StudProgramRaspored
# dict(UUID, StudProgramRaspored) = FakultetRaspored (id programa -> studProgramRaspored)

@dataclass
class RasporedDan(ReadWrite):
    danNum: int
    redovi: list[RasporedRed]

    @classmethod
    def from_json(cls, data):
        danNum = int(data['danNum'])
        redovi = list(map(RasporedRed.from_json, data['redovi']))
        return cls(danNum, redovi)

### Studijski programi ###
@dataclass
class Semestar(ReadWrite):
    semestarNum: int
    dani: dict[int, RasporedDan]

    @classmethod
    def from_json(cls, data):
        semestarNum = int(data['semestarNum'])
        dani = data['dani']
        for key, dan in dani.items():
            dani[key] = RasporedDan.from_json(dan)
        return cls(semestarNum, dani)

@dataclass
class StudProgramRaspored(ReadWrite):
    studProgramNaziv: str
    studProgramStepenStudija: str
    semestri: dict[int, Semestar] # godina -> semestar

    @classmethod
    def from_json(cls, data):
        studProgramNaziv = str(data['studProgramNaziv'])
        studProgramStepenStudija = str(data['studProgramStepenStudija'])
        semestri = data['semestri']
        for key, semestar in semestri.items():
            semestri[key] = Semestar.from_json(semestar)
        return cls(studProgramNaziv, studProgramStepenStudija, semestri)

@dataclass
class StudProgramiRaspored(ReadWrite):
    semestar: str # 'Z'/'L' (zimski ili letnji)
    studProgrami: dict[str, StudProgramRaspored] # studProgramId -> studProgramRaspored

    @classmethod
    def from_json(cls, data):
        semestar = str(data['semestar'])
        studProgrami = data['studProgrami']
        for key, studProgram in studProgrami.items():
            studProgrami[key] = StudProgramRaspored.from_json(studProgram)
        return cls(semestar, studProgrami)

### Prostorije ###
@dataclass
class ProstorijaRaspored(ReadWrite):
    prostorijaOznaka: str
    dani: dict[int, RasporedDan]

    @classmethod
    def from_json(cls, data):
        prostorijaOznaka = str(data['prostorijaOznaka'])
        dani = data['dani']
        for key, dan in dani.items():
            dani[key] = RasporedDan.from_json(dan)
        return cls(prostorijaOznaka, dani)

@dataclass
class ProstorijeRaspored(ReadWrite):
    semestar: str
    prostorije: dict[str, ProstorijaRaspored] # prostorijaId -> prostorijaRaspored

    @classmethod
    def from_json(cls, data):
        semestar = str(data['semestar'])
        prostorije = data['prostorije']
        for key, prostorija in prostorije.items():
            prostorije[key] = ProstorijaRaspored.from_json(prostorija)
        return cls(semestar, prostorije)

### Predavaci ###
@dataclass
class PredavacRaspored(ReadWrite):
    predavacIme: str
    dani: dict[int, RasporedDan]
    
    @classmethod
    def from_json(cls, data):
        predavacIme = str(data['predavacIme'])
        dani = data['dani']
        for key, dan in dani.items():
            dani[key] = RasporedDan.from_json(dan)
        return cls(predavacIme, dani)

@dataclass
class PredavaciRaspored(ReadWrite):
    semestar: str
    predavaci: dict[str, PredavacRaspored] # predavacId -> predavacRaspored

    @classmethod
    def from_json(cls, data):
        semestar = str(data['semestar'])
        predavaci = data['predavaci']
        for key, predavac in predavaci.items():
            predavaci[key] = PredavacRaspored.from_json(predavac)
        return cls(semestar, predavaci)


### Net Liste ###
@dataclass
class NetListaStudProgramGodina:
    raspored: list[NetListaRed]

@dataclass
class NetListaStudProgram:
    studProgramGodinaListe: dict[str, NetListaStudProgramGodina] # {1: lista, 2: lista}

@dataclass
class NetListeRaspored:
    semestar: str
    studProgramListe: dict[str, NetListaStudProgram] # {ANI: {1:lista, 2:lista}, SIIT: {1:lista, 2:lista}}


# EDIT mode:
#     07:00 07:15 07:30 ...
# 101 ko drzi, ko slusa (smer - oznaka+stepen+nivo, godina, grupe), tipNastave, sta (oznaka predmeta+plan, naziv)
        # (id predavaca, id grupa -> kako bi se proverilo preklapanje)
# 102
# 103

@dataclass
class PredmetPrikaz:
    idPred: str
    oznakaPred: str
    planPred: str
    nazivPred: str

@dataclass
class PredavacPrikaz:
    idPredavac: str  # (bitno za premestanje, da bi se okinula provera zadovoljenosti pravila)
    predavac: str

@dataclass
class StudProgram:
    oznakaStudProg: str
    stepenStudProg: str
    nivoStudProg: str
    godina: int

    def __hash__(self):
        return hash(str(self.oznakaStudProg) + str(self.stepenStudProg) + str(self.nivoStudProg))

@dataclass
class StudGrupa:
    idGrupe: str
    oznakaGrupe: int

@dataclass
class EditPrikaz:
    idMeeting: str
    tipNastave:str
    predmet: PredmetPrikaz
    predavac: PredavacPrikaz
    studProgrami: list[StudProgram] # set studProgram-a
    studGrupe: list[StudGrupa] # list guid-a  (bitno za premestanje, da bi se okinula provera zadovoljenosti pravila)

    studBr: int
    prekoracenKapacitet: int # prekoracen kapacitet prostorije

    def __str__(self):
        # predmet, predavac, tipNastave, studProgramOznake, prekoracenKapacitet -> diktira i boju
        studProgramOznake = [studProgram.oznakaStudProg for studProgram in self.studProgrami]
        studGrupaOznake = [studGrupa.oznakaGrupe for studGrupa in self.studGrupe]
        return f'Tip nastave: {self.tipNastave},\npredmet: {self.predmet.nazivPred},\n' + \
                f'predavac: {self.predavac.predavac},\nstudijski programi: {studProgramOznake},\n' + \
                  f'broj grupa: {len(self.studGrupe)},\noznake grupa: {studGrupaOznake}, \n' + \
                    f'ukupan broj stud: {self.studBr}, \nprekoracenje: {self.prekoracenKapacitet}'


# Google Calendar prikaz
# -> Start Date format zavisi od konfiguracije Google naloga -> moze doci do gresaka prilikom importa
# .csv fajl

# Subject, Start Date, Start Time, End Date, End Time, All Day Event, Description, Location, Private
# Proba, 05/12/2022, 12:00, 05/12/2022, 13:30, False, Proba integracije, NTP-311, False

@dataclass
class GoogleCalendarPrikaz:
    naslov: str # vrstaNastave + nazivPred
    datumPocetka: str
    datumKraja: str
    vremePocetka: str
    vremeKraja: str
    opis: str # nazivSmer + studGrupa
    lokacija: str # prostorija
    ceoDan: bool
    privatan: bool

    def to_dict(self):
        return {
            'Subject':       self.naslov,
            'Start Date':    self.datumPocetka,
            'Start Time':    self.vremePocetka,
            'End Date':      self.datumKraja,
            'End Time':      self.vremeKraja,
            'All Day Event': self.ceoDan,
            'Description':   self.opis,
            'Location':      self.lokacija,
            'Private':       self.privatan,
        }
