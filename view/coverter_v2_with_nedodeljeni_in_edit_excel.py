# %% [markdown]
# # Glavna skripta komponente za izvoze podataka

# %% [markdown]
#  #### Formatiranje termina
#  - 9_format_termini.ipynb

# %% [markdown]
#  ### Formatiranje termina u model za prikazivanje

# %% [markdown]
#  #### Metode za mapiranje

# %%
from model_parser import ReadWrite, MeetingSchedule, RasporedPrikaz
from model_joined import *
from model_prikaz import *
from parser_utils import *


# %%
from collections import defaultdict


# %%
import numpy as np
import pandas as pd

# %%
def time_grain_index_to_time(
        grain_index: int,
        grains_per_day: int, 
        start_hour: int
) -> str:
    while grain_index > grains_per_day:
        grain_index -= (grains_per_day + 1)
    start_time = start_hour * 60
    time = start_time + grain_index * 15
    hour = time // 60
    minute = time % 60
    return f'{hour:02d}:{minute:02d}'


# %%
def minute_to_time(
        minutes: int
) -> str:
    hour = minutes // 60
    minute = minutes % 60
    return f'{hour:02d}:{minute:02d}'


# %%
def predavac_to_ispis(
        predavac: Predavac
) -> str:
    if predavac.titula:
        return f'{predavac.prezime} {predavac.titula} {predavac.ime}'
    return f'{predavac.prezime} {predavac.ime}'


# %%
def predavac_to_oznaka(
        predavac: Predavac
) -> str:
    return str(predavac.oznaka)


# %%
def stud_grupe_to_ispis(
        stud_grupe: list[StudentskaGrupa],
        bi_weekly: bool,
        tip_nastave: str
) -> str:
    # TODO: preuzmi sve grupe za taj studijski program i tu godinu
    # ako su iste duzine, vrati 'SVI', inace vrati spojen ispis grupa
    # bitno da li je svake druge nedelje
    # za sada vraca sve ako je predavanje jer nemamo izborne predmete
    if tip_nastave == 'PRED':
        return 'SVI'
    oznake = [grupa.oznaka for grupa in stud_grupe]
    if bi_weekly:
        first_week = oznake[:len(oznake)//2]
        second_week = oznake[len(oznake)//2:]
        first_week = ', '.join(first_week)
        second_week = ', '.join(second_week)
        return f'{first_week}({second_week})'
    else:
        return ', '.join(oznake)


# %%
def meeting_assignment_to_dan(
        ma: MeetingAssignmentJoined
) -> str:
    return ma.startingTimeGrain.dan.danUNedelji


# %%
def meeting_assignment_to_prostorija_id(
        ma: MeetingAssignmentJoined
) -> str:
    return ma.prostorija.id


# %%
def meeting_assignment_to_prostorija_zauzece(
        ma: MeetingAssignmentJoined,
) -> ProstorijaZauzece:
    prostorija_oznaka = ma.prostorija.oznaka
    first_time_grain = ma.startingTimeGrain.grainIndex
    duration_in_grains = ma.meeting.durationInGrains
    last_time_grain = first_time_grain + duration_in_grains
    return ProstorijaZauzece(prostorija_oznaka, first_time_grain, last_time_grain)

# %%
def meeting_assignment_to_stud_grupe(
        ma: MeetingAssignmentJoined
) -> list[tuple[str, int]]:
    # lista tuplova => [(studProgramId, godina)]
    stud_program_godine = []
    stud_grupe = ma.meeting.studentskeGrupe
    stud_program_ids = set()
    for grupa in stud_grupe:
        stud_program_id = grupa.studijskiProgram.id
        godina = grupa.godina
        # samo jednom dodajemo informacije o studijskom programu i godini
        if stud_program_id in stud_program_ids:
            continue
        stud_program_ids.add(stud_program_id)
        stud_program_godine.append((stud_program_id, godina))
    return stud_program_godine


# %%
def meeting_assignment_to_predavaci_ids(
        ma: MeetingAssignmentJoined
) -> list[str]:
    predavac_id = ma.meeting.predavac.id
    ostali_predavaci = ma.meeting.ostaliPredavaci
    predavaci_ids = [pred.id for pred in ostali_predavaci]
    predavaci_ids.append(predavac_id)
    return predavaci_ids


# %%
def meeting_assignment_to_red(
        ma: MeetingAssignmentJoined,
        grains_per_day: int,
        start_hour: int
) -> Red:
    start_time_grain = ma.startingTimeGrain
    # ako optimizator nije uspeo da dodeli vreme
    if start_time_grain is None:
        return None
    start_time_grain = start_time_grain.grainIndex
    duration_in_grains = ma.meeting.durationInGrains
    end_time_grain = start_time_grain + duration_in_grains - 1
    tip_nastave = ma.meeting.meetingTip
    predmet_naziv = ma.meeting.predmet.naziv

    stud_grupa = stud_grupe_to_ispis(ma.meeting.studentskeGrupe, ma.meeting.biWeekly, tip_nastave)
    vreme_pocetka = time_grain_index_to_time(start_time_grain, grains_per_day, start_hour)
    vreme_kraja = time_grain_index_to_time(end_time_grain, grains_per_day, start_hour)
    
    return Red(stud_grupa, vreme_pocetka, vreme_kraja, tip_nastave, predmet_naziv)


# %%
def meeting_assignment_to_prostorija_red(
        ma: MeetingAssignmentJoined,
        grains_per_day: int,
        start_hour: int
) -> ProstorijaRed:
    red = meeting_assignment_to_red(ma, grains_per_day, start_hour)
    if red is None:
        return None
    
    stud_grupe = ma.meeting.studentskeGrupe
    # moze za vezbe, za predavanja imamo spojene stud programe - ALI TO NIKOME NIJE BITNO
    odsek = stud_grupe[0].studijskiProgram.naziv
    godina = stud_grupe[0].godina
    semestar_oznaka = stud_grupe[0].semestar
    semestar = arabic_to_roman(godina * 2 - 1 if semestar_oznaka == 'Z' else godina * 2)
    predavac = predavac_to_ispis(ma.meeting.predavac)
    ostali_predavaci = [predavac_to_ispis(predavac) for predavac in ma.meeting.ostaliPredavaci]
    if len(ostali_predavaci):
        predavaci = f'{predavac}, ' + ', '.join(ostali_predavaci)
    else:
        predavaci = predavac
    
    red.odsek = odsek
    red.semestar = semestar
    red.predavac = predavaci
    return ProstorijaRed(**vars(red))


# %%
def meeting_assignment_to_predavac_red(
        ma: MeetingAssignmentJoined,
        grains_per_day: int,
        start_hour: int
) -> PredavacRed:
    red = meeting_assignment_to_red(ma, grains_per_day, start_hour)
    if red is None:
        return None

    prostorija = ma.prostorija.oznaka
    stud_grupe = ma.meeting.studentskeGrupe
    # moze za vezbe, za predavanja imamo spojene stud programe - ALI TO NIKOME NIJE BITNO
    odsek = stud_grupe[0].studijskiProgram.naziv
    godina = stud_grupe[0].godina
    semestar_oznaka = stud_grupe[0].semestar
    semestar = arabic_to_roman(godina * 2 - 1 if semestar_oznaka == 'Z' else godina * 2)
    
    red.prostorija = prostorija
    red.odsek = odsek
    red.semestar = semestar
    return PredavacRed(**vars(red))


# %%
def meeting_assignment_to_raspored_red(
        ma: MeetingAssignmentJoined,
        grains_per_day: int,
        start_hour: int
) -> RasporedRed:
    red = meeting_assignment_to_red(ma, grains_per_day, start_hour)
    if red is None:
        return None

    prostorija = ma.prostorija.oznaka
    predavac = predavac_to_ispis(ma.meeting.predavac)
    ostali_predavaci = [predavac_to_ispis(predavac) for predavac in ma.meeting.ostaliPredavaci]
    if len(ostali_predavaci):
        predavaci = f'{predavac}, ' + ', '.join(ostali_predavaci)
    else:
        predavaci = predavac
    
    red.prostorija = prostorija
    red.predavac = predavaci
    return RasporedRed(**vars(red))


# %%
def meeting_assignment_to_edit_prikaz(
        ma: MeetingAssignmentJoined
) -> EditPrikaz:
    meeting_id = ma.id

    prostorija_kapacitet = ma.prostorija.kapacitet
    potreban_kapacitet = ma.meeting.requiredCapacity
    prekoracen_kapacitet = 0
    if potreban_kapacitet > prostorija_kapacitet:
        prekoracen_kapacitet = potreban_kapacitet - prostorija_kapacitet
    
    nastava_tip = ma.meeting.meetingTip
    
    predmet = ma.meeting.predmet
    predmet_prikaz = PredmetPrikaz(predmet.id, predmet.oznaka, predmet.plan, predmet.naziv)
    
    predavac_fullname = predavac_to_ispis(ma.meeting.predavac)
    predavac_prikaz = PredavacPrikaz(ma.meeting.predavac.id, predavac_fullname)

    stud_grupe = ma.meeting.studentskeGrupe
    stud_programi = set()
    stud_grupe_list = []
    for grupa in stud_grupe:
        stud_program = grupa.studijskiProgram
        stud_programi.add(StudProgram(stud_program.oznaka, stud_program.stepen, stud_program.nivo, grupa.godina))
        stud_grupe_list.append(StudGrupa(grupa.id, grupa.oznaka))
    
    return EditPrikaz(meeting_id, nastava_tip, predmet_prikaz, predavac_prikaz, list(stud_programi), 
                        stud_grupe_list, potreban_kapacitet, prekoracen_kapacitet)


# %%
def unassigned_meeting_assignment_to_edit_prikaz(
        ma: MeetingAssignmentJoined
) -> EditPrikaz:
    meeting_id = ma.id

    potreban_kapacitet = ma.meeting.requiredCapacity

    trajanje_termina = ma.meeting.durationInGrains

    nastava_tip = ma.meeting.meetingTip
    
    predmet = ma.meeting.predmet
    predmet_prikaz = PredmetPrikaz(predmet.id, predmet.oznaka, predmet.plan, predmet.naziv)
    
    predavac_fullname = predavac_to_ispis(ma.meeting.predavac)
    predavac_prikaz = PredavacPrikaz(ma.meeting.predavac.id, predavac_fullname)

    stud_grupe = ma.meeting.studentskeGrupe
    stud_programi = set()
    stud_grupe_list = []
    for grupa in stud_grupe:
        stud_program = grupa.studijskiProgram
        stud_programi.add(StudProgram(stud_program.oznaka, stud_program.stepen, stud_program.nivo, grupa.godina))
        stud_grupe_list.append(StudGrupa(grupa.id, grupa.oznaka))
    # staviti max int umesto -1 da se ne bi bojila polja
    return EditPrikaz(meeting_id, nastava_tip, predmet_prikaz, predavac_prikaz, list(stud_programi), 
                        stud_grupe_list, potreban_kapacitet, -1, trajanje_termina)


# %% [markdown]
#  ### Kreiranje **Raspored prikaza**
# 
#  - transformacija ```MeetingAssignment``` u ```StudProgramiRaspored```

# %%
def stepen_nivo_to_stud_program_stepen_studija(
        stepen: int, 
        nivo: int
) -> str:
    if stepen == 1 and nivo == 1:
        stepen_studija = "oas"
    if stepen == 1 and nivo == 2:
        stepen_studija = "oss"
    if stepen == 2 and nivo == 1:
        stepen_studija = "mas"
    if stepen == 2 and nivo == 5:
        stepen_studija = "mss"
    return stepen_studija


# %%
# u slucaju novih 2-godisnjih master stud programa, dodati ga u listu
# TODO: (izmena da informacija o tome da li je stud program cuva u samom programu)
def is_dvogodisnji_master(
        oznaka: str
) -> bool:
    return oznaka in ["AI1", "AI2", "AI3", "AI4", "AI5", "AI6", "AI7", "AI8"]


# %%
def create_dani_dict():
    dani = {}
    for i in range(0, 6):
        dani[i] = RasporedDan(i, [])
    return dani


# %%
def create_semestar(
        semestar_num: int,
        start_semestar: int
) -> Semestar:
    semestar = Semestar(start_semestar + (semestar_num - 1) *2, dict())
    semestar.dani = create_dani_dict()
    return semestar


# %%
def create_semestri(
        stud_program_raspored: StudProgramRaspored, 
        oznaka: str, 
        stepen: int, 
        nivo: int, 
        start_semestar: int
) -> StudProgramRaspored:
    # oas i oss
    if stepen == 1:
        # 4 semestra za oas, 3 za oss
        for i in range(1, 5):
            semestar = create_semestar(i, start_semestar)
            # semestri[godina] = semestar
            stud_program_raspored.semestri[i] = semestar
            if nivo == 2 and i == 3:
                break
    # mas i mss
    if stepen == 2:
        # 1 semestar za jednogodisnje, 2 za dvogodisnje
        for i in range(1, 3):
            semestar = create_semestar(i, start_semestar)
            # semestri[4+godina] = semestar jer su studentske grupe na masteru 5. i 6. godina
            stud_program_raspored.semestri[4+i] = semestar
            if nivo == 1 and i == 1 and not is_dvogodisnji_master(oznaka):
                break
    return stud_program_raspored


# %%
def meeting_assignments_to_stud_programi_raspored(
        semestar_oznaka: str, 
        stud_programi: list[StudijskiProgram], 
        meeting_assignments: list[MeetingAssignmentJoined],
        grains_per_day: int, 
        start_hour: int, 
        unassigned_file_path: str,
        dir_path: str = '../out_data/'
) -> StudProgramiRaspored:
    start_semestar = 1 if semestar_oznaka == "Z" else 2

    # kreiranje strukture
    raspored = StudProgramiRaspored(semestar_oznaka, dict())
    for stud_program in stud_programi:
        stepen_studija = stepen_nivo_to_stud_program_stepen_studija(stud_program.stepen, stud_program.nivo)
        # kreiranje rasporeda za studijski program
        stud_program_raspored = StudProgramRaspored(stud_program.naziv, stepen_studija, dict())
        # dodavanje rasporeda za studijski program u sve rasporede
        raspored.studProgrami[stud_program.id] = stud_program_raspored
        # kreiranje semestara za studijski program
        stud_program_raspored = create_semestri(stud_program_raspored, stud_program.oznaka, stud_program.stepen, stud_program.nivo, start_semestar)
        
    # dodavanje MeetingAssignment-a u dane
    ma_unassigned = []
    for ma in meeting_assignments:
        raspored_red = meeting_assignment_to_raspored_red(ma, grains_per_day, start_hour)
        if raspored_red is None:
            ma_unassigned.append(ma)
            continue
        # neophodno naci u koje sve studijske programe treba dodati red
        # (posto studentske grupe mogu biti iz vise studijskih programa)
        dan_num = meeting_assignment_to_dan(ma)
        stud_program_godine = meeting_assignment_to_stud_grupe(ma)
        # programGodina => (studProgramId, godina)
        for program_godina in stud_program_godine:
            # dodavanje redova
            stud_program_id = program_godina[0]
            godina = program_godina[1]
            stud_program_raspored = raspored.studProgrami[stud_program_id]
            semestar = stud_program_raspored.semestri[godina]
            semestar.dani[dan_num].redovi.append(raspored_red)
    
    # sortiranje po vremenu (9:00-20:00)
    for stud_program_raspored in raspored.studProgrami.values():
        for semestar in stud_program_raspored.semestri.values():
            for dan in semestar.dani.values():
                dan.redovi.sort(key=lambda red: red.vremePocetka)
    
    # zapisivanje nedodeljenih ma za rucnu dodelu
    # ReadWrite.write_to_file(ma_unassigned, unassigned_file_path, dir_path)

    return raspored


# %% [markdown]
#  ### Kreiranje **Prostorije raspored prikaza**
# 
#  - transformacija ```MeetingAssignment``` u ```ProstorijeRaspored```

# %%
def meeting_assignments_to_prostorije_raspored(
        semestar: int, 
        prostorije: list[Prostorija], 
        meeting_assignments: list[MeetingAssignmentJoined], 
        grains_per_day: int, 
        start_hour: int, 
        unassigned_file_path: str,
        dir_path: str = '../out_data/'
) -> ProstorijeRaspored:
    # kreiranje strukture
    raspored = ProstorijeRaspored(semestar, dict())
    for prostorija in prostorije:
        prostorija_raspored = ProstorijaRaspored(prostorija.oznaka, create_dani_dict())
        raspored.prostorije[prostorija.id] = prostorija_raspored

    # dodavanje MeetingAssignment-a u dane
    ma_unassigned = []
    for ma in meeting_assignments:
        prostorija_red = meeting_assignment_to_prostorija_red(ma, grains_per_day, start_hour)
        if prostorija_red is None:
            ma_unassigned.append(ma)
            continue
        # dodati red u odgovarajucu prostoriju za odgovarajuci dan
        dan_num = meeting_assignment_to_dan(ma)
        prostorija_id = meeting_assignment_to_prostorija_id(ma)
        prostorija = raspored.prostorije[prostorija_id]
        prostorija.dani[dan_num].redovi.append(prostorija_red)

    # sortiranje po vremenu (9:00-20:00)
    for prosotrija_raspored in raspored.prostorije.values():
        for dan in prosotrija_raspored.dani.values():
            dan.redovi.sort(key=lambda red: red.vremePocetka)
    
    # zapisivanje nedodeljenih ma za rucnu dodelu
    # ReadWrite.write_to_file(ma_unassigned, unassigned_file_path, dir_path)

    return raspored


# %% [markdown]
#  ### Kreiranje **Predavaci raspored prikaza**
# 
#  - transformacija ```MeetingAssignment``` u ```PredavaciRaspored```

# %%
def meeting_assignments_to_predavaci_raspored(
        semestar: int, 
        predavaci: list[Predavac], 
        meeting_assignments: list[MeetingAssignmentJoined], 
        grains_per_day: int, 
        start_hour: int, 
        unassigned_file_path: str,
        dir_path: str = '../out_data/'
) -> PredavaciRaspored:
    # kreiranje strukture
    raspored = PredavaciRaspored(semestar, dict())
    for predavac in predavaci:
        predavac_raspored = PredavacRaspored(predavac_to_ispis(predavac), create_dani_dict())
        raspored.predavaci[predavac.id] = predavac_raspored

    # dodavanje MeetingAssignment-a u dane
    ma_unassigned = []
    for ma in meeting_assignments:
        predavac_red = meeting_assignment_to_predavac_red(ma, grains_per_day, start_hour)
        if predavac_red is None:
            ma_unassigned.append(ma)
            continue
        # dodati red svim predavacima za odgovarajuci dan
        dan_num = meeting_assignment_to_dan(ma)
        predavac_ids = meeting_assignment_to_predavaci_ids(ma)
        for predavac_id in predavac_ids:
            predavac = raspored.predavaci[predavac_id]
            predavac.dani[dan_num].redovi.append(predavac_red)

    # sortiranje po vremenu (9:00-20:00)
    for predavacRaspored in raspored.predavaci.values():
        for dan in predavacRaspored.dani.values():
            dan.redovi.sort(key=lambda red: red.vremePocetka)
    
    # zapisivanje nedodeljenih ma za rucnu dodelu
    # ReadWrite.write_to_file(ma_unassigned, unassigned_file_path, dir_path)

    return raspored


# %% [markdown]
#  ### Kreiranje **Google kalendar prikaza**
# 
#  - transformacija ```MeetingAssignment``` u ```GoogleCalendarPrikaz```

# %%
from datetime import datetime, timedelta
from copy import copy

# pocetniDan mora biti u formatu '%d/%m/%Y'
def meeting_assignment_to_predavac_google_red(
        ma: MeetingAssignmentJoined,
        grains_per_day: int, 
        start_hour: int, 
        pocetni_dan: str, 
        repeat_num: int = 1):
    datum_format = '%d/%m/%Y'
    # naslov
    meeting = ma.meeting
    tip_nastave = meeting.meetingTip
    predmet_naziv = meeting.predmet.naziv
    naslov = tip_nastave + ', ' + predmet_naziv

    # datumi
    pocetni_dan = datetime.strptime(pocetni_dan, datum_format).date()
    dan_num = meeting_assignment_to_dan(ma)
    datum_pocetka = (pocetni_dan + timedelta(days=dan_num)).strftime(datum_format)
    datum_kraja = datum_pocetka

    # vremena
    start_time_grain = ma.startingTimeGrain.grainIndex
    duration_in_grains = ma.meeting.durationInGrains
    end_time_grain = start_time_grain + duration_in_grains - 1
    vreme_pocetka = time_grain_index_to_time(start_time_grain, grains_per_day, start_hour)
    vreme_kraja = time_grain_index_to_time(end_time_grain, grains_per_day, start_hour)

    # opis
    stud_grupe = meeting.studentskeGrupe
    odsek = stud_grupe[0].studijskiProgram.naziv
    godina = stud_grupe[0].godina
    stud_grupa = stud_grupe_to_ispis(stud_grupe, meeting.biWeekly, tip_nastave)
    opis = odsek + ', ' + str(godina) + '. godina, grupe: ' + stud_grupa

    # lokacija
    lokacija = ma.prostorija.oznaka

    cal_prikaz = GoogleCalendarPrikaz(naslov, datum_pocetka, datum_kraja, vreme_pocetka, vreme_kraja, opis, lokacija, False, False)
    # vrati listu termina * broj nedelja
    # uvecaj datum za 7 dana za svaku nedelju
    prikazi = [cal_prikaz]
    for i in range(repeat_num - 1):
        cal_next_prikaz = copy(cal_prikaz)
        # (0 + 1) * 7 = pomera_nedelja_unapred
        # pomeraj_nedelja_unapred + pomeraj_od_pocetnog_dana
        sledeciDan = (pocetni_dan + timedelta(days=(i + 1) * 7 + dan_num)).strftime(datum_format)
        cal_next_prikaz.datumPocetka = sledeciDan
        cal_next_prikaz.datumKraja = sledeciDan
        prikazi.append(cal_next_prikaz)
    
    return prikazi


# %%
def meeting_assignments_to_predavac_google_calendar(
        meeting_assignments: list[MeetingAssignmentJoined],
        predavac_id: str,
        pocetni_dan: str, 
        repeat_num: int,
        grains_per_day: int, 
        start_hour: int
):
    raspored = []
    for ma in meeting_assignments:
        if ma.startingTimeGrain is None:
            continue
        predavac_ids = meeting_assignment_to_predavaci_ids(ma)
        if predavac_id in predavac_ids:
            raspored.extend(meeting_assignment_to_predavac_google_red(ma, grains_per_day, start_hour, pocetni_dan, repeat_num))
    return raspored


# %%
def write_google_calendar_csv(
        filePath: str,
        meeting_assignments: list[MeetingAssignmentJoined], 
        predavac_id: str, 
        pocetni_dan: str, 
        repeat_num: int, 
        grains_per_day: int, 
        start_hour: int
) -> None:
    # columns = ['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'All Day Event', 'Description', 'Location', 'Private']
    raspored = meeting_assignments_to_predavac_google_calendar(
        meeting_assignments, predavac_id, pocetni_dan, repeat_num, grains_per_day, start_hour)
    df = pd.DataFrame.from_records([r.to_dict() for r in raspored])
    df.to_csv(filePath, index=False)


# %% [markdown]
#  ### Kreiranje prikaza za **Edit-ovanje**
# 
#  - zauzece prostorija po time-grains (podeoci od 15 minuta)
#  - prikaz celog mitinga u svakom time-grain koji zauzima

# %%
def generate_grains_per_day(
        start_idx: int, 
        count_per_day: int
) -> list[int]:
    day = []
    for j in range(count_per_day):
        day.append(start_idx * count_per_day + j)
    return day


# %%
def generate_grains(
        day_count: int, 
        count_per_day: int
) -> tuple[list[int], list[int]]:
    grains_per_day = []
    all_grains = []
    for i in range(day_count):
        day = []
        day = generate_grains_per_day(i, count_per_day)
        grains_per_day.append(day)
        all_grains.extend(day)
    return grains_per_day, all_grains


# %%
def meeting_assignments_to_edit_view(
        meeting_assignments: list[MeetingAssignmentJoined], 
        day_num: int, 
        grains_per_day: int
) -> dict[str, dict[int, EditPrikaz]]:
    grains_per_day, all_grains = generate_grains(day_num, grains_per_day)
    prostorija_odrzavanje = defaultdict(lambda: all_grains.copy())
    for ma in meeting_assignments:
        if ma.startingTimeGrain is None:
            continue
        zauzece = meeting_assignment_to_prostorija_zauzece(ma)
        # dodajemo zauzece na odgovarajuci time grain
        # -> vreme kada su slobodne ostaju indeksi
        odrzavanje = meeting_assignment_to_edit_prikaz(ma)
        for timeGrain in range(zauzece.firstTimeGrainIndex, zauzece.lastTimeGrainIndex):
            prostorija_odrzavanje[zauzece.prostorijaOznaka][timeGrain] = odrzavanje
    return prostorija_odrzavanje



# %%
def unassigned_meeting_assignments_to_edit_view(
        meeting_assignments: list[MeetingAssignmentJoined], 
) -> list[EditPrikaz]:
    odrzavanja = []
    for ma in meeting_assignments:
        if ma.startingTimeGrain is None:
            nedodeljeno_odrzavanje = unassigned_meeting_assignment_to_edit_prikaz(ma)
            odrzavanja.append(nedodeljeno_odrzavanje)
    return odrzavanja

# %%
def create_columns(
        grains_per_day: int, 
        start_hour: int
) -> list[str]:
    grains = generate_grains_per_day(0, grains_per_day)
    # dodavanje kolone za oznaku
    columns = ['Oznaka'] + [time_grain_index_to_time(grain, grains_per_day, start_hour) for grain in grains]
    return columns


# %%
def create_prostorija_row(
        day_num: int, 
        grains_per_day: int, 
        weekly_zauzece
):
    # dobavi sve za odredjeni dan
    start_grain = day_num * grains_per_day
    end_grain = start_grain + grains_per_day
    daily_zauzece = weekly_zauzece[start_grain:end_grain]
    # napravi lep to string za objekat
    daily_prikaz = [str(zauzece) if type(zauzece) != int else '' for zauzece in daily_zauzece]
    return daily_prikaz


# %%
def create_all_rows(
        day_num: int, 
        grains_per_day: int, 
        all_zauzeca
):
    all_rows = []
    for oznaka, prostorija_zauzece in all_zauzeca.items():
        all_rows.append([str(oznaka)] + create_prostorija_row(day_num, grains_per_day, prostorija_zauzece))
    return all_rows


# %%
def create_day_edit(
        day_num: int, 
        grains_per_day: int, 
        start_hour: int, 
        all_zauzeca
):
    columns = create_columns(grains_per_day, start_hour)
    rows = create_all_rows(day_num, grains_per_day, all_zauzeca)
    return columns, rows


# %%
def style_cell(
        value: str, 
        ok, warn, danger
):
    if 'prekoracenje: -1' in value:
        return
    if 'PRED' in value and 'prekoracenje: 0' not in value:
        return warn
    if ('AUD' in value or 'RAC' in value or 'LAB' in value) and 'prekoracenje: 0' not in value:
        return danger
    if 'prekoracenje: 0' in value:
        return ok


# %%
def style_workbook(
        writer: pd.ExcelWriter,
        dan: int
):
    # formatiranje
    workbook = writer.book
    # column width
    worksheet = writer.sheets[dan]
    worksheet.set_default_row(188.5)
    worksheet.set_row(0, 14.5)
    worksheet.set_column('B:BJ', 20)
    # freeze header and first column
    worksheet.freeze_panes(1, 1)
    # merge cells
    merge_ok_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bg_color': '#D8E4BC', 'border': 1, 'text_wrap': True})
    merge_warn_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bg_color': '#FDE9D9', 'border': 1, 'text_wrap': True})
    merge_danger_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bg_color': '#E6B8B7', 'border': 1, 'text_wrap': True})
    return worksheet, merge_ok_format, merge_warn_format, merge_danger_format

# %%
from copy import copy
def write_nedodeljeni_edit_view(
        nedodeljeno_odrzavanje: list[EditPrikaz],
        grains_per_day: int,
        start_hour: int,
):
    columns = create_columns(grains_per_day, start_hour)
    rows = []
    # red je prazna lista duzine broja kolona sa praznim stringovima
    # u svaki red treba upisati po jedan nedodeljeni termin
    # u duzini od prvog column do duzine trajanja
    row = [''] * len(columns)
    for odrzavanje in nedodeljeno_odrzavanje:
        start_index = 1
        end_index = start_index + odrzavanje.duzinaTrajanja
        current_row = copy(row)
        for time_grain in range(start_index, end_index):
            current_row[time_grain] = str(odrzavanje)
        rows.append(current_row)

    return columns, rows

# %%
def write_edit_view(
        prostorija_odrzavanje,
        nedodeljeno_odrzavanje: list[EditPrikaz],
        file_name: str,
        dir_path: str = '../out_data/'
):
    grains_per_day = 60 + 1 # 60 grains po danu + 1 za poslednju pauzu
    start_hour = 7
    dani = ['PON', 'UTO', 'SRE', 'CET', 'PET', 'SUB', 'NEDODELJENI']

    # pravi ove normalne sheet-ove
    # nova funkcija ce napraviti nedodeljeni sheet
    with pd.ExcelWriter(dir_path + file_name + '.xlsx', engine='xlsxwriter') as writer:
        for idx, dan in enumerate(dani):
            if idx == 6:
                columns, rows = write_nedodeljeni_edit_view(nedodeljeno_odrzavanje, grains_per_day, start_hour)
            else:
                columns, rows = create_day_edit(idx, grains_per_day, start_hour, prostorija_odrzavanje)
            df = pd.DataFrame(rows, columns=columns)
            df.to_excel(writer, sheet_name=dan, index=False)
            # formatiranje celog dokumenta
            worksheet, merge_ok_format, merge_warn_format, merge_danger_format = style_workbook(writer, dan)

            for row_idx, row in enumerate(rows):
                # print(row)
                # print()
                # za svaki red
                current_meeting = ''
                merge_start = 0
                merge_end = 0
                for col_idx, meeting in enumerate(row):
                    # ignorisi prvu vrednost (ime prostorije)
                    if col_idx == 0:
                        continue
                    # zapamti prvo pojavljivanje (ime i broj kolone -> B2)
                    if current_meeting == '' and meeting != '':
                        current_meeting = meeting
                        merge_start = col_idx
                        merge_end = merge_start
                    
                    # sve dok je isto, uvecavaj broj kolone (B2++)
                    if current_meeting == meeting:
                        merge_end = col_idx
                    # naisao na novo
                    else:
                        # odradi merge
                        style = style_cell(current_meeting, merge_ok_format, merge_warn_format, merge_danger_format)
                        worksheet.merge_range(row_idx+1, merge_start, row_idx+1, merge_end, current_meeting, style)
                        # resetuj vrednosti na novi
                        current_meeting = meeting
                        merge_start = col_idx
                        merge_end = merge_start
                # merge poslednjeg ako nije prazno
                if current_meeting != '':
                    style = style_cell(current_meeting, merge_ok_format, merge_warn_format, merge_danger_format)
                    worksheet.merge_range(row_idx+1, merge_start, row_idx+1, merge_end, current_meeting, style)


# %% [markdown]
#  #### Prikaz termina
#  - 10_prikaz_termina.ipynb

# %% [markdown]
#  #### Rad sa fajlovima
# 
#  - zapisivanje tekstualnog sadržaja u fajl
#  - čitanje tekstualnog sadržaja iz fajla

# %%
def write_to_file(
        content: str,
        file_name: str,
        extension: str = 'html',
        dir_path: str = '../out_data/'
) -> None:
    with open(dir_path + file_name + '.' + extension, 'w', encoding='utf-8') as out_file:
        out_file.write(content)


# %% [markdown]
#  #### Stilizovanje rasporeda
#  - ```styles.css```

# %% [markdown]
#  #### HTML to PDF

# %%
import pdfkit
from unidecode import unidecode

# %%
def write_pdf_from_html(
        file_name: str,
        css_path: str,
        dir_path: str = '../out_data/',
        lib_path: str = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
) -> None:
    file_path = dir_path + file_name + '.html'
    out_path = dir_path + file_name + '.pdf'
    config = pdfkit.configuration(wkhtmltopdf=lib_path)
    options = {
        "enable-local-file-access": "", 
        "encoding": "UTF-8",
        "page-size": "A4", 
        "title": "Raspored",
        "margin-top": "10mm", 
        "margin-bottom": "10mm",
        "margin-right": "10mm",
        "margin-left": "10mm"
    }
    pdfkit.from_file(file_path, options=options, css=css_path, output_path=out_path, configuration=config)


# %% [markdown]
#  ### HTML raspored

# %%
def dan_num_to_dan(
        dan_num: int
) -> str:
    dani = {
        0: "ponedeljak", 
        1: "utorak", 
        2: "sreda",
        3: "četvrtak",
        4: "petak",
        5: "subota"
    }
    return dani[dan_num]


# %%
def semestar_num_to_semestar(
        semestar_num: int
) -> str:
    return str(semestar_num) + '. semestar'


# %%
def oznaka_stepena_to_stepen_studija(
        oznaka_stepena: str
) -> str:
    stepeni = {
        "oss": "osnovne strukovne studije",
        "mss": "master strukovne studije",
        "oas": "osnovne akademske studije",
        "mas": "master akademske studije"
    }
    return stepeni[oznaka_stepena]


# %%
def vrsta_nastave_to_naziv_nastave(
        vrsta_nastave: str
) -> str:
    vrste_nastave = {
        "PRED": "Pred.",
        "AUD": "aud.vežbe",
        "RAC": "rač.vežbe",
        "LAB": "lab.vežbe"
    }
    return vrste_nastave[vrsta_nastave]


# %%
# Grupa-e	Od	Do	Učionica	Vrsta nast.	Naziv predmeta	Izvođač
def raspored_red_to_ispis(
        red: RasporedRed
) -> list[str]:
    return [red.studGrupa, red.vremePocetka, red.vremeKraja, \
        red.prostorija, vrsta_nastave_to_naziv_nastave(red.vrstaNastave), \
        red.nazivPred, red.predavac]


# %%
# Grupa-e	Od	Do	Odsek	Sem.	Vrsta nast.	Naziv Predmeta	Izvođač
def prostorija_red_to_ispis(
        red: ProstorijaRed
) -> list[str]:
    return [red.studGrupa, red.vremePocetka, red.vremeKraja, \
        red.odsek, red.semestar, vrsta_nastave_to_naziv_nastave(red.vrstaNastave), \
        red.nazivPred, red.predavac]


# %%
# Grupa-e	Od	Do	Učionica	Odsek	Sem.	Vrsta nast.	Naziv Predmeta
def predavac_red_to_ispis(
        red: PredavacRed
) -> list[str]:
    return [red.studGrupa, red.vremePocetka, red.vremeKraja, \
        red.prostorija, red.odsek, red.semestar, \
        vrsta_nastave_to_naziv_nastave(red.vrstaNastave), red.nazivPred]


# %%
def stud_program_header(
        cols: int, 
        day: str
) -> str:
    # head
    table = '  <thead>\n'
    # title
    table += '    <tr><th colspan="' + str(cols) + '" class="day">' + day + '</th></tr>\n'
    # header
    table += '    <tr><th>Grupa-e</th><th>Od</th><th>Do</th>' + \
            '<th>Učionica</th><th>Vrsta nast.</th>' + \
            '<th>Naziv predmeta</th><th>Izvođač</th></tr>\n'
    table += '  </thead>\n'
    return table


# %%
def prostorija_header(
        cols: int, 
        day: str
) -> str:
    # head
    table = '  <thead>\n'
    # title
    table += '    <tr><th colspan="' + str(cols) + '" class="day">' + day + '</th></tr>\n'
    # header
    table += '    <tr><th>Grupa-e</th><th>Od</th><th>Do</th>' + \
            '<th>Odsek</th><th>Sem.</th><th>Vrsta nast.</th>' + \
            '<th>Naziv predmeta</th><th>Izvođač</th></tr>\n'
    table += '  </thead>\n'
    return table


# %%
def predavac_header(
        cols: int, 
        day: str
) -> str:
    # head
    table = '  <thead>\n'
    # title
    table += '    <tr><th colspan="' + str(cols) + '" class="day">' + day + '</th></tr>\n'
    # header
    table += '    <tr><th>Grupa-e</th><th>Od</th><th>Do</th>' + \
            '<th>Učionica</th><th>Odsek</th><th>Sem.</th><th>Vrsta nast.</th>' + \
            '<th>Naziv predmeta</th></tr>\n'
    table += '  </thead>\n'
    return table


# %%
def stud_program_colgroup() -> str:
    # colgroup
    table = '<colgroup>'
    table += '<col class="eleven" />'
    table += '<col class="seven" />'
    table += '<col class="seven" />'
    table += '<col class="ten" />'
    table += '<col class="ten" />'
    table += '<col class="thirty" />'
    table += '<col class="twenty-five" />'
    table += '</colgroup>'
    return table


# %%
def prostorija_colgroup() -> str:
    # colgroup
    table = '<colgroup>'
    table += '<col class="eleven" />'
    table += '<col class="seven" />'
    table += '<col class="seven" />'
    table += '<col class="fifteen" />'
    table += '<col class="five" />'
    table += '<col class="ten" />'
    table += '<col class="twenty-five" />'
    table += '<col class="twenty" />'
    table += '</colgroup>'
    return table


# %%
def predavac_colgroup() -> str:
    # colgroup
    table = '<colgroup>'
    table += '<col class="eleven" />'
    table += '<col class="seven" />'
    table += '<col class="seven" />'
    table += '<col class="ten" />'
    table += '<col class="twenty" />'
    table += '<col class="five" />'
    table += '<col class="ten" />'
    table += '<col class="thirty" />'
    table += '</colgroup>'
    return table


# %%
def table_head(
        day: int, 
        type: str
) -> str:
    if type == 'studProgram':
        colgroup = stud_program_colgroup()
        head = stud_program_header(7, day)
    if type == 'prostorija':
        colgroup = prostorija_colgroup()
        head = prostorija_header(8, day)
    if type == 'predavac':
        colgroup = predavac_colgroup()
        head = predavac_header(8, day)
    return colgroup + head


# %%
def html_table(
        rows: list[str],
        day: str,
        type: str
) -> str:
    table = '<table>'
    table += table_head(day, type)
    # body
    table += '  <tbody>\n'
    for row in rows:
        table += '    <tr><td>'
        table += '</td><td>'.join(row)
        table += '</td></tr>\n'
    table += '  </tbody>\n'
    table += '</table>\n'
    return table


# %%
def html_head() -> str:
    html = '<html>'
    # head
    html += '<head>'
    # utf-8
    html += '<meta http-equiv="Content-type" content="text/html; charset=utf-8" />'
    # stylesheet
    html += '<link rel="stylesheet" href="styles.css">'
    html += '</head>'
    return html


# %%
def stud_program_tables(
        raspored: StudProgramiRaspored
) -> str:
    stud_program_tables = {}
    for stud_program_id, stud_program in raspored.studProgrami.items():
        html = ''
        stud_program_naziv = stud_program.studProgramNaziv
        stepen_studija = stud_program.studProgramStepenStudija
        html += '<h1>Raspored predavanja - ' + oznaka_stepena_to_stepen_studija(stepen_studija)
        html += '<h1>' + stud_program_naziv + '</h1>'
        for semestar in stud_program.semestri.values():
            semestar_num = semestar.semestarNum
            semestar_html = ''
            for dan in semestar.dani.values():
                dani_html = ''
                if len(dan.redovi) != 0:
                    rows_list = [raspored_red_to_ispis(dan) for dan in dan.redovi]
                    dani_html += html_table(rows_list, dan_num_to_dan(dan.danNum), 'studProgram')
                    dani_html += '<br/>'
                semestar_html += dani_html
            if semestar_html:
                semestar_html = '<div class="page">' + semestar_html
                semestar_html = '<h2 class="right">' + semestar_num_to_semestar(semestar_num) + '</h2>' + semestar_html
                semestar_html += '</div>'
                semestar_html += '<br/>'
            html += semestar_html
        html += '<br/>'
        stud_program_tables[stud_program_id] = html
    return stud_program_tables


# %%
def prostorija_table(
        raspored: ProstorijaRaspored
) -> str:
    html = html_head()
    prostorija_oznaka = raspored.prostorijaOznaka
    html += '<h1>Zauzeće prostorije - ' + str(prostorija_oznaka) + '</h1>'
    for dan in raspored.dani.values():
        dani_html = ''
        if len(dan.redovi) != 0:
            rows_list = [prostorija_red_to_ispis(dan) for dan in dan.redovi]
            dani_html += html_table(rows_list, dan_num_to_dan(dan.danNum), 'prostorija')
            dani_html += '<br/>'
        html += dani_html
    html += '</body></html>'
    return html


# %%
def predavac_table(
        raspored: PredavacRaspored
) -> str:
    html = html_head()
    predavac_ime = raspored.predavacIme
    html += '<h1>Raspored predavača - ' + predavac_ime + '</h1>'
    for dan in raspored.dani.values():
        dani_html = ''
        if len(dan.redovi) != 0:
            rowsList = [predavac_red_to_ispis(dan) for dan in dan.redovi]
            dani_html += html_table(rowsList, dan_num_to_dan(dan.danNum), 'predavac')
            dani_html += '<br/>'
        html += dani_html
    html += '</body></html>'
    return html


# %% [markdown]
#  ### Mapiranje rasporeda studijskih programa

# %%
def html_generator(
        stud_program_ids: list[str],
        raspored: StudProgramiRaspored
) -> str:
    html = html_head()
    # body
    html += '<body>'
    # studProgramId: htmlTabele
    stud_program_tables_map = stud_program_tables(raspored)
    # [studProgamId1, studProgramId2]
    for stud_program_id in stud_program_ids:
        # nadji u mapi po id-u i konkateniraj
        if stud_program_id in stud_program_tables_map.keys():
            html += stud_program_tables_map.get(stud_program_id)
    html += '</body></html>'
    return html


# %%
def generate_all_rasporedi(
        raspored: StudProgramiRaspored,
        raspored_combinations: list[RasporedPrikaz],
        dir_path: str = '../out_data/rasporedi/studenti/',
        css: str = 'styles.css'
) -> None:
    css_file = dir_path + css

    for combination in raspored_combinations:
        html = html_generator(combination.studProgrami, raspored)
        file_name = unidecode(combination.nazivRasporeda)
        html_file = 'html'
        write_to_file(html, file_name, html_file, dir_path)
        write_pdf_from_html(file_name, css_file, dir_path)
        print(combination.nazivRasporeda + ' DONE')


# %% [markdown]
#  ### Mapiranje svih prostorija rasporeda

# %%
def generate_all_prostorija_rasporedi(
        raspored: ProstorijeRaspored,
        dir_path: str = '../out_data/rasporedi/prostorije',
        css: str = 'styles.css'
):
    css_file = dir_path + css

    for prostorija in raspored.prostorije.values():
        oznaka = str(prostorija.prostorijaOznaka)
        oznaka_clean = oznaka.replace('.', ' ').replace('/', ' ')
        file_name = unidecode(oznaka_clean)
        html = prostorija_table(prostorija)
        html_file = 'html'
        write_to_file(html, file_name, html_file, dir_path)
        write_pdf_from_html(file_name, css_file, dir_path)
        print(oznaka + ' DONE')
    


# %% [markdown]
#  ### Mapiranje svih predavac rasporeda

# %%
def generate_all_predavac_rasporedi(
        raspored: PredavaciRaspored,
        dir_path: str = '../out_data/rasporedi/predavaci',
        css: str = 'styles.css'
):
    css_file = dir_path + css

    for predavac in raspored.predavaci.values():
        ime = predavac.predavacIme
        file_name = unidecode(ime)
        html = predavac_table(predavac)
        html_file = 'html'
        write_to_file(html, file_name, html_file, dir_path)
        write_pdf_from_html(file_name, css_file, dir_path)
        print(ime + ' DONE')



# %% [markdown]
#  ### Primer izvršavanja
#  - potrebno je ucitati celokupan MeetingSchedule (koji sadrzi liste entiteta)
#    - od listi entiteta su potrebne:
#        - studProgramList
#        - prostorijaList
#        - predavacList
#    - pored toga, potrebna informacija o semestru -> 'Z' ili 'L'
#  (ako je jednostavnije, moze se izmeniti metoda tako da prima direktno liste i oznaku semestra -> da se ne bi kreirao ceo MeetingSchedule objekat)
#  - potrebno je proslediti listu MeetingAssignment objekata koja se dobija od optimizatora
#    - mapiranje je pravljeno po izlazu iz optimizatora
#  - BITNO I NOVO: potrebno je proslediti listu RasporedPrikaz objekata
#    - ovi objekti sadrze id-eve studijskih programa koji treba da budu u okviru istog rasporeda
#    - mogu se samo cuvati u bazi, mozemo racunati da se ne menjaju (nema potrebe za podrskom kroz UI)
#  Kako bi se pokrenuo kod, neophodno je instalirati potrebne Python zavisnosti
#    - requirements.txt fajl
#    - zgodno kreirati virtuelno okruzenje i u okviru njega ih instalirati
#  Potrebno je postaviti styles.css fajl u svim folderima u kojima ce biti zapisani fajlovi
#    - skripta ne vraca nista, samo kreira fajlove
#  Za kreiranje PDF fajlova je potreban dodatni softver
#    - za rad lokalnog testiranja, mogu se samo zakomentarisati linije koje kreiraju PDF fajlove

# %%
def generate_all(
        schedule: MeetingSchedule,
        meeting_assignments: list[MeetingAssignmentJoined],
        raspored_combinations: list[RasporedPrikaz],
        out_dir_path: str,
        grains_per_day: int = 60,
        start_hour: int = 7,
        day_num: int = 6
):
    unassigned_file_name = 'nedodeljeni_termini'
    # RASPORED
    raspored = meeting_assignments_to_stud_programi_raspored(schedule.semestar, schedule.studProgramList, meeting_assignments, grains_per_day, start_hour, unassigned_file_name, out_dir_path)
    generate_all_rasporedi(raspored, raspored_combinations, out_dir_path + 'studenti/')
    # RASPORED ZA PROSTORIJE
    prostorije_raspored = meeting_assignments_to_prostorije_raspored(schedule.semestar, schedule.prostorijaList, meeting_assignments, grains_per_day, start_hour, unassigned_file_name, out_dir_path)
    generate_all_prostorija_rasporedi(prostorije_raspored, out_dir_path + 'prostorije/')
    # RASPORED ZA PREDAVACE
    predavaci_raspored = meeting_assignments_to_predavaci_raspored(schedule.semestar, schedule.predavacList, meeting_assignments, grains_per_day, start_hour, unassigned_file_name, out_dir_path)
    generate_all_predavac_rasporedi(predavaci_raspored, out_dir_path + 'predavaci/')


    # EDIT PRIKAZ
    grains_per_day_edit = grains_per_day + 1
    prostorija_odrzavanje = meeting_assignments_to_edit_view(meeting_assignments, day_num, grains_per_day_edit)
    nedodeljeno_odrzavanje = unassigned_meeting_assignments_to_edit_view(meeting_assignments)
    file_name = 'edit_raspored_prikaz'
    write_edit_view(prostorija_odrzavanje, nedodeljeno_odrzavanje, file_name, out_dir_path)


# %%
schedule = MeetingSchedule.read_entity_from_file('4_svi_fajlovi_spojeni')
meeting_assignments = MeetingAssignmentJoined.read_list_from_file('8_optimized_oas')
raspored_combinations = RasporedPrikaz.read_list_from_file('2_rasporedi_spajanje_plan')

# meeting_assignments = MeetingAssignmentJoined.read_list_from_file('for_formatting/ma_oas')

# %%
generate_all(schedule, meeting_assignments, raspored_combinations, '../out_data/rasporedi/')

# generate_all(None, meeting_assignments, None, '../out_data/rasporedi/')
print('=== FINISHED ===')

# %%



