# %%
import uuid
from itertools import combinations
from collections import defaultdict

# %%
from model_parser import *
from realizacija_linked_model import *

# %%
from dataclasses import dataclass

@dataclass
class ComboPredmet:
    oznaka_predmeta: str
    plan_predmeta: int
    predavac_id: str
    ostali_predavaci: str
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            getattr(other, 'oznaka_predmeta', None) == self.oznaka_predmeta and
            getattr(other, 'plan_predmeta', None) == self.plan_predmeta and
            getattr(other, 'predavac_id', None) == self.predavac_id and
            getattr(other, 'ostali_predavaci', None) == self.ostali_predavaci)

    def __hash__(self):
        return hash(self.oznaka_predmeta + str(self.plan_predmeta) + self.predavac_id + self.ostali_predavaci)

@dataclass
class ComboStudGrupe:
    stud_grupe: list[str]
    total_count: int

# %% [markdown]
# ### Generisanje predavanja na osnovu realizacije i parsiranih fajlova

# %%
# trebalo bi da nalazi najbolji spoj predavanja ispod limita

# arr = [(id, count), (id, count)]
# limit = number
# returns: highest combo below limit
# ( ( (id, count), (id, count) ), total_count )
def find_array_max_below_limit(arr, limit):
    combos = []
    for i in range(len(arr)):
        combos.extend(list(combinations(arr, i+1)))
    combo_sums = []
    for combo in combos:
        combo_sums.append(sum(c[1] for c in combo))

    combined = []
    for i in range(len(combos)):
        combined.append((combos[i], combo_sums[i]))
    
    combined.sort(key=lambda x: x[1])
    
    highest = combined[0]
    for com in combined:
        if com[1] > limit:
            break
        if com[1] >= highest[1]:
            highest = com
    
    return highest

# %%
def get_grupe_id_size_for_stud_program_godina(
        stud_program_id: str,
        godina: int,
        stud_grupe: list[StudentskaGrupa]
) -> ComboStudGrupe:
    # lista id-eva grupa, ukupan broj studenata u tim grupama
    stud_grupe_ids = [x.id for x in stud_grupe if x.studijskiProgram == stud_program_id and x.godina == godina]
    total_stud_count = sum(x.brojStudenata for x in stud_grupe if x.studijskiProgram == stud_program_id and x.godina == godina)
    return ComboStudGrupe(stud_grupe_ids, total_stud_count)

# %%
def create_predavanja_for_predmet(
        predmet: Predmet,
        profesor_id: str,
        ostali_predavaci: list[str],
        stud_grupe_ids: list[str]
) -> list[Meeting]:
    meetings = []
    if predmet.brojCasovaPred > 0 and predmet.brojCasovaPred < 4:
        # kreiraj jedan miting za sve grupe
        meetings.append(Meeting(str(uuid.uuid4()), 'AUD', 'PRED', predmet.brojCasovaPred, profesor_id, ostali_predavaci, predmet.id, stud_grupe_ids))
    elif predmet.brojCasovaPred == 4:
        # kreiraj dva mitinga za sve grupe
        meetings.append(Meeting(str(uuid.uuid4()), 'AUD', 'PRED', 2, profesor_id, ostali_predavaci, predmet.id, stud_grupe_ids))
        meetings.append(Meeting(str(uuid.uuid4()), 'AUD', 'PRED', 2, profesor_id, ostali_predavaci, predmet.id, stud_grupe_ids))
    elif predmet.brojCasovaPred == 5:
        # kreiraj dva mitinga po 3/2 za sve grupe
        meetings.append(Meeting(str(uuid.uuid4()), 'AUD', 'PRED', 3, profesor_id, ostali_predavaci, predmet.id, stud_grupe_ids))
        meetings.append(Meeting(str(uuid.uuid4()), 'AUD', 'PRED', 2, profesor_id, ostali_predavaci, predmet.id, stud_grupe_ids))
    elif predmet.brojCasovaPred == 6:
        # 6 casova predavanja (samo scenska, sve zajedno)
        meetings.append(Meeting(str(uuid.uuid4()), 'AUD', 'PRED', 6, profesor_id, ostali_predavaci, predmet.id, stud_grupe_ids))
    return meetings

# %%
def combine_studijski_programi(
        realizacija: Realizacija,
        stud_programi: list[StudijskiProgram], 
        stud_grupe: list[StudentskaGrupa],
        stepen: int
) -> dict[ComboPredmet, dict[str, ComboStudGrupe]]:
    # (oznaka_predmeta, plan_predmeta, predavac_id, ostali_predavaci) -> { stud_program_id: ([sg1_id, sg2_id], total_cnt) }
    # predavanja se spajaju na svim studijskim programima gde se poklapaju: oznaka_predmeta + plan_predmeta + predavaci
    combined = defaultdict(lambda: {})
    for stud_program_predmeti in realizacija.studijskiProgramPredmeti:
        stud_program_id = stud_program_predmeti.studijskiProgramId
        stud_program = next(x for x in stud_programi if x.id == stud_program_id)
        # stepen=1 -> OAS, stepen=2 -> MAS
        if stud_program.stepen == stepen:
            for predmet_predavac in stud_program_predmeti.predmetPredavaci:
                # pronadji sve studentske grupe za studijski program i godinu
                combo_stud_grupe = get_grupe_id_size_for_stud_program_godina(
                    stud_program_predmeti.studijskiProgramId, predmet_predavac.predmetGodina, stud_grupe)
                # ako nema upisanih, preskoci
                if combo_stud_grupe.total_count == 0:
                    continue
                ostali_profesori = ','.join(predmet_predavac.ostaliProfesori)
                combo_predmet = ComboPredmet(predmet_predavac.predmetOznaka, predmet_predavac.predmetPlan, predmet_predavac.profesorId, ostali_profesori)
                combined[combo_predmet][stud_program_id] = combo_stud_grupe
    return combined


# %%
def find_grupe_ids_from_counts(
        stud_grupe_counts: list[ComboStudGrupe]
) -> list[str]:
    stud_grupe_ids = []
    for stud_grupa_count in stud_grupe_counts:
        stud_grupe_ids.extend(stud_grupa_count.stud_grupe)
    return stud_grupe_ids

# %%
def create_predavanja_for_combo(
        # [ (stud_program_id, count), (stud_program_id, count) ]
        stud_program_stud_count: list[tuple[str, int]],
        # { stud_program_id: ([sg1_id, sg2_id], total_cnt) }
        stud_program_grupe: dict[str, ComboStudGrupe],
        # ( ( (stud_program_id, count), (stud_program_id, count) ), total_count )
        combo: tuple[tuple[str, int], int],
        predmet: Predmet,
        profesor_id: str,
        ostli_profesori_ids: list[str]
) -> list[Meeting]:
    meetings = []

    combo_stud_program_ids = [program[0] for program in combo[0]]
    # ako nisu svi studijski programi ukljuceni u combo
    if len(stud_program_stud_count) - len(combo_stud_program_ids) > 0:
        # kreiraj predavanja za izostavljenje
        svi_stud_program_ids = [program[0] for program in stud_program_stud_count]
        preostali_stud_program_ids = list(set(svi_stud_program_ids) - set(combo_stud_program_ids))
        
        # za svaki preostali studijski program, nadji grupe
        stud_grupe_counts = [stud_program_grupe.get(id) for id in preostali_stud_program_ids]
        stud_grupe_ids = find_grupe_ids_from_counts(stud_grupe_counts)
        izostavljeno_predavanje = create_predavanja_for_predmet(predmet, profesor_id, ostli_profesori_ids, stud_grupe_ids)
        meetings.extend(izostavljeno_predavanje)
    
    # kreiranje combo predavanja
    stud_grupe_counts = [stud_program_grupe.get(id) for id in combo_stud_program_ids]
    stud_grupe_ids = find_grupe_ids_from_counts(stud_grupe_counts)
    combo_predavanje = create_predavanja_for_predmet(predmet, profesor_id, ostli_profesori_ids, stud_grupe_ids)
    meetings.extend(combo_predavanje)

    return meetings

# %%
def create_predavanja_with_combined(
        realizacija: Realizacija,
        stud_programi: list[StudijskiProgram],
        stud_grupe: list[StudentskaGrupa],
        prostorije: list[Prostorija],
        predmeti: list[Predmet],
        stepen: int = 1
) -> list[Meeting]:
    predavanja = combine_studijski_programi(realizacija, stud_programi, stud_grupe, stepen)

    # za svako od potencijalno spojenih predavanja, proveri da li je ukupan broj studenata veci od A1
    # (da ne bismo spojili SIIT, IN i E2 u jedan termin - za recimo mreze)
    student_limit = max(prostorija.kapacitet for prostorija in prostorije)

    meetings = []
    # generisanje termina za spojena predavanja sa sto boljim zauzecem prostorije
    for predmet_profesori, stud_program_grupe in predavanja.items():
        # (oznaka_predmeta, plan_predmeta, predavac_id, ostali_predavaci)
        predmet = next(x for x in predmeti if x.oznaka == predmet_profesori.oznaka_predmeta)
        profesor = predmet_profesori.predavac_id
        ostali_profesori = predmet_profesori.ostali_predavaci.split(',')
        # { stud_program_id: ([sg1_id, sg2_id], total_cnt) }
        
        stud_program_stud_count = []
        for stud_program_id, stud_grupe_total_count in stud_program_grupe.items():
            stud_program_stud_count.append((stud_program_id, stud_grupe_total_count.total_count))
        best_combo = find_array_max_below_limit(stud_program_stud_count, student_limit)
        meetings.extend(create_predavanja_for_combo(stud_program_stud_count, stud_program_grupe, best_combo, predmet, profesor, ostali_profesori))
    return meetings

# %% [markdown]
# ### Generisanje vežbi na osnovu realizacije i parsiranih fajlova

# %%
def get_grupe_for_stud_program_godina(
        stud_program_id: str,
        godina: int,
        stud_grupe: list[StudentskaGrupa]      
) -> tuple[StudentskaGrupa, int]:
    found_stud_grupe = [x for x in stud_grupe if x.studijskiProgram == stud_program_id and x.godina == godina]
    total_stud_count = sum(x.brojStudenata for x in stud_grupe if x.studijskiProgram == stud_program_id and x.godina == godina)
    return (found_stud_grupe, total_stud_count)

# %%
def get_asistent(
        asistent_zauzeca: list[AsistentZauzeca]
) -> str:
    # generator
    # vraca id asistenta iz liste koji ima preostalih slobodnih termina
    # kada dostupnih termina, vraca uvek prvog
    for asistent in asistent_zauzeca:
        termini = asistent.brojTermina
        for _ in range(termini):
            id = asistent.asistentId
            yield id
    while True:
        yield asistent_zauzeca[0].asistentId 

# %%
def get_velika_rac_prostorija(
        prostorije: list[Prostorija]
) -> dict[str, list[int]]:
    # { katedra_id: [15, 20, 11] }
    # mapiranje katedre na dostupne velike ucionice
    # nadji sve racunarske ucionice od 32 mesta i popuni dictionary mapiranje katedra na broj slobodnih sati
    # (2 na ACS-u, 1 na IIM, 2 opste)
    # dostupnost ucionice: 7-22 * 5 dana = 15*5 = 75 sati
    sati_nedeljno = (22-7) * 5
    dostupnost = defaultdict(list)
    for prostorija in prostorije:
        if prostorija.tip == 'RAC' and prostorija.kapacitet == 32:
            # preuzmi organizacionu jedinicu cija je katedra
            org_jedinica = prostorija.orgJedinica
            # ako nije u vlasnistvu, smesti u opste
            if org_jedinica == None:
                org_jedinica = 'opsta'
            # ako ima vise vlasnika, uzmi prvu
            if type(org_jedinica) == list:
                org_jedinica = org_jedinica[0]
            dostupnost[org_jedinica].append(sati_nedeljno)
    return dostupnost

# %%
def available_velika_rac_prostorija(
        prostorije: list[Prostorija],
) -> bool:
    dostupnost = get_velika_rac_prostorija(prostorije)
    while True:
        (predavac_org_jed, trajanje) = yield
        available = False
        # dobavi za predavace veliku ucionicu ako postoji za njegovu katedru i ako ima slobodnog vremena
        org_jedinica_prostorije = dostupnost[predavac_org_jed]
        dostupna_idx = next((idx for idx, dostupno_sati in enumerate(org_jedinica_prostorije) if dostupno_sati >= trajanje), None)
        if dostupna_idx != None:
            org_jedinica_prostorije[dostupna_idx] -= trajanje
            available = True
        # ako nije slobodna, probaj opste
        else:
            opste_prostorije = dostupnost['opsta']
            dostupna_idx = next((idx for idx, dostupno_sati in enumerate(opste_prostorije) if dostupno_sati >= trajanje), None)
            if dostupna_idx != None:
                opste_prostorije[dostupna_idx] -= trajanje
                available = True
        yield available

# %%
def create_tip_vezbe(
        predmet_id: str,
        stud_grupe: list[StudentskaGrupa],
        tip_vezbe: str,
        trajanje_vezbe: int,
        min_per_meeting: int,
        max_per_meeting: int,
        asistent_generator
) -> list[Meeting]:
    meetings = []
    spajanje = []
    # ako vezbe imaju 1 cas => odrzavaju se svake dve nedelje po 2 casa
    bi_weekly = trajanje_vezbe == 1
    # ako je bi_weekly, max broj studenata se duplira jer ce dolaziti neizmenicno
    if bi_weekly:
        min_per_meeting = min_per_meeting * 2
        max_per_meeting = max_per_meeting * 2
    for stud_grupa in stud_grupe:
        if stud_grupa.brojStudenata > min_per_meeting:
            # grupa ima minimum min_per_meeting osobe => kreiramo 1 miting za grupu
            asistent_id = next(asistent_generator)
            meetings.append(Meeting((str(uuid.uuid4())), tip_vezbe, tip_vezbe, trajanje_vezbe, asistent_id, [], predmet_id, stud_grupa.id, bi_weekly))
        else:
            # grupa je manje od min_per_meeting osobe => spajamo grupe tako da dobijemo mitinge od maksimum max_per_meeting osoba
            # dodaj u listu grupa za spajanje
            spajanje.append((stud_grupa.id, stud_grupa.brojStudenata))
    # trazi najbolji kombo koji ima maksimum max_per_meeting osobe sve dok imas nekoga u listi za spajanje
    # izbacuj iz liste one koje preuzmes u best combo
    while len(spajanje) > 0:
        best_combo = find_array_max_below_limit(spajanje, max_per_meeting)
        combo_grupe = [grupa for grupa in best_combo[0]]
        spajanje = [grupa for grupa in spajanje if grupa not in combo_grupe]
        combo_ids = [grupa[0] for grupa in combo_grupe]
        asistent_id = next(asistent_generator)
        meetings.append(Meeting(str(uuid.uuid4()), tip_vezbe, tip_vezbe, trajanje_vezbe, asistent_id, [], predmet_id, combo_ids, bi_weekly))
    return meetings
    

# %%
def create_vezbe_for_predmet(
        predmet: Predmet,
        asistent_zauzeca: list[AsistentZauzeca],
        stud_grupe: list[StudentskaGrupa],
        org_jedinica: str,
        available_velika_rac_prostorija_generator
) -> list[Meeting]:
    # min i max propisani statutom fakulteta
    min_per_aud_meeting = 32
    max_per_aud_meeting = 50 # 64 je ali ne zelimo da spojimo 4 grupe od 16, vec da imamo 3+2
    min_per_lab_meeting = 12
    max_per_lab_meeting = 16
    min_per_rac_meeting = 12
    max_per_rac_meeting = 16

    meetings = []
    aud = predmet.brojCasovaAud
    lab = predmet.brojCasovaLab
    rac = predmet.brojCasovaRac

    asistent_generator = get_asistent(asistent_zauzeca)

    # auditorne
    if aud != -1 and aud <= 3:
        meetings.extend(create_tip_vezbe(predmet.id, stud_grupe, 'AUD', aud, min_per_aud_meeting, max_per_aud_meeting, asistent_generator))
    if aud > 3:
        meetings.extend(create_tip_vezbe(predmet.id, stud_grupe, 'AUD', aud, min_per_aud_meeting, max_per_aud_meeting, asistent_generator))
        meetings.extend(create_tip_vezbe(predmet.id, stud_grupe, 'AUD', aud, min_per_aud_meeting, max_per_aud_meeting, asistent_generator))

    # laboratorijske
    if lab != -1:
        # ako je grupa manja od 12, spoj ih do max 12, ako nije, stavi je samu
        meetings.extend(create_tip_vezbe(predmet.id, stud_grupe, 'LAB', lab, min_per_lab_meeting, max_per_lab_meeting, asistent_generator))
    
    # racunarske
    if rac != -1:
        next(available_velika_rac_prostorija_generator)
        # ako postoji dostupih velikih ucionica, povecaj max_per_rac_meeting i umanji slobodne ucionice
        if available_velika_rac_prostorija_generator.send((org_jedinica, len(stud_grupe) * rac)):
            max_per_rac_meeting = max_per_rac_meeting * 2
        meetings.extend(create_tip_vezbe(predmet.id, stud_grupe, 'RAC', rac, min_per_rac_meeting, max_per_rac_meeting, asistent_generator))

    return meetings

# %%
# stepen oznacava stepen studija -> 1=OAS, 2=MAS
def create_vezbe(
        realizacija: Realizacija,
        stud_programi: list[StudijskiProgram],
        stud_grupe: list[StudentskaGrupa],
        prostorije: list[Prostorija], 
        predmeti: list[Predmet],
        predavaci: list[Predavac],
        stepen: int = 1
) -> list[Meeting]:
    meetings = []
    # kreiranje generatora za dostupnost velikih ucionica
    available_velika_rac_prostorija_generator = available_velika_rac_prostorija(prostorije)
    for stud_program_predmeti in realizacija.studijskiProgramPredmeti:
        stud_program_id = stud_program_predmeti.studijskiProgramId
        # na osnovu stud_program_id nadji studijski program i proveri da li je OAS ili MAS
        stud_program = next(x for x in stud_programi if x.id == stud_program_id)
        # stepen=1 -> OAS, stepen=2 -> MAS
        if stud_program.stepen == stepen:
            for predmet_predavac in stud_program_predmeti.predmetPredavaci:
                predmet = next(x for x in predmeti if x.id == predmet_predavac.predmetId)
                asistentZauzeca = predmet_predavac.asistentZauzeca
                # pronadji za studijski program + godina sve studentske grupe
                studGrupe, total = get_grupe_for_stud_program_godina(
                    stud_program_id, predmet_predavac.predmetGodina, stud_grupe)
                # ako nema upisanih, preskoci
                if total == 0:
                    continue
                # pronadji org jedinicu za asistenta da bi pronasao veliku prostoriju ako postoji za tu org jedinicu
                org_jedinica_id = None
                if predmet.brojCasovaRac != -1:
                    org_jedinica_id = next(x.orgJedinica for x in predavaci if x.id == asistentZauzeca[0].asistentId)

                meetings.extend(create_vezbe_for_predmet(predmet, asistentZauzeca, studGrupe, org_jedinica_id, available_velika_rac_prostorija_generator))
    return meetings

# %%
def create_nastava(
        realizacija: Realizacija, 
        stud_programi: list[StudijskiProgram],
        stud_grupe: list[StudentskaGrupa],
        prostorije: list[Prostorija],
        predmeti: list[Predmet], 
        predavaci: list[Predavac],
        stepen: int = 1):
    predavanjaList = create_predavanja_with_combined(
        realizacija, stud_programi, stud_grupe, prostorije, predmeti, stepen)
    vezbeList = create_vezbe(
        realizacija, stud_programi, stud_grupe, prostorije, predmeti, predavaci, stepen)
    return predavanjaList + vezbeList

# %% [markdown]
# ### Demonstracija upotrebe
# ### TODO: integrisati poziv funkcije u okviru Java koda
# - funkcija koja treba biti pozvana je create_nastava
# - funkcija prima realizaciju i liste entiteta (studijski programi, studentske grupe, prostorije, predmeti i predavaci)
# - funkcija prima i int vrednost stepen studija (1 ili 2, to jest OAS ili MAS)
# - funkcija vraca generisanu listu termina (meeting-a)


# %%
schedule = MeetingSchedule.read_entity_from_file('4_svi_fajlovi_spojeni')
schedule_izmene = MeetingSchedule.read_entity_from_file('4_svi_fajlovi_spojeni')

realizacija = Realizacija.read_entity_from_file('6_realizacija_bez_izbornih')
realizacija_izmene = Realizacija.read_entity_from_file('6_realizacija_bez_izbornih')

meetings_oas = create_nastava(
    realizacija, schedule.studProgramList, schedule.studentskaGrupaList, schedule.prostorijaList, schedule.predmetList, schedule.predavacList, 1)
meeting_mas = create_nastava(
    realizacija, schedule.studProgramList, schedule.studentskaGrupaList, schedule.prostorijaList, schedule.predmetList, schedule.predavacList, 2)

# 2550 sada, pre 2616
# 604 sada, pre 545
print(len(meetings_oas))
print(len(meeting_mas))

# %% [markdown]
# ### Zapisivanje u fajl generisanih termina uz sve ostale parsirane podatke

# %%
schedule.meetingList = meetings_oas
ReadWrite.write_to_file(schedule, '7_schedule_oas')
schedule.meetingList = meeting_mas
ReadWrite.write_to_file(schedule, '7_schedule_mas')

# %%



