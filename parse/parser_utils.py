### Utility funkcije za parsiranje

import math
import re
from transliterate import translit

# transformacije rimskih u arapske brojeve
def roman_to_arab(roman_num: str) -> int:
    roman_arab_dict = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}
    return roman_arab_dict[roman_num]

def arabic_to_roman(arabic):
    arab_roman_dict = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'}
    return arab_roman_dict[arabic]

# transformacija broja semstra (6) u godinu (3)
def semestar_to_godina(semestar: int) -> int:
    godina = math.ceil(semestar / 2)
    return godina

# transformacija broja semstra (6) i oznaku (L/Z)
def semestar_to_oznaka(semestar: int) -> str:
    semestar = 'L' if semestar % 2 == 0 else 'Z'
    return semestar


# transformacija cirilicnih slova u latinicna
def cyrilic_to_latin(text):
    latin = translit(text, language_code='sr', reversed=True)
    return latin


def remove_new_line(text):
    without_new_line = text.replace('\\n', ' ').replace('\n', ' ').replace('\t',' ').replace('\\', ' ')
    return without_new_line

def remove_extra_whitespace(text):
    without_extra_whitespace = re.sub(r'\s+', ' ', text)
    without_extra_whitespace = without_extra_whitespace.strip()
    return without_extra_whitespace

def title_to_lowercase(text):
    with_title_lowercase = re.sub(r'\sMr\s', ' mr ', text)
    return with_title_lowercase

'''
funkcija koja mapira broj 15-ica na broj casova
# 1 30 - dvocas vezbe (45 45)                           = 15 * 6
# 1 45 - dvocas predavanje (45 45 + 15)                 = 15 * 7
# 2 30 - trocas vezbe (45 45 45 + 15)                   = 15 * 10
# 2 45 - trocas predavanja (45 45 45 + 15 15)           = 15 * 11
# 3 15 - cetvorocas vezbe (45 45 45 45 + 15)            = 15 * 13
# 3 45 - cetvorocas predavanje (45 45 45 45 + 15 15 15) = 15 * 15
'''
def map_class_lengths(num_of_15s:int) -> int:
    """Mapira trajanje casova iz broja 15-minutnih perioda u broj casova sa pauzama

    Parameters
    ----------
    num_of_15s: broj 15-minutnih perioda

    Mapping
    ----------
    # 45   - jednocas vezbe (45)                            = 15 * 3
    # 1 30 - dvocas vezbe (45 45)                           = 15 * 6
    # 1 45 - dvocas predavanje (45 45 + 15)                 = 15 * 7
    # 2 30 - trocas vezbe BEZ PAUZE (45 45 45)              = 15 * 9
    # 2 30 - trocas vezbe (45 45 45 + 15)                   = 15 * 10
    # 2 45 - trocas predavanja (45 45 45 + 15 15)           = 15 * 11
    # 3 15 - cetvorocas vezbe (45 45 45 45 + 15)            = 15 * 13
    # 3 45 - cetvorocas predavanje (45 45 45 45 + 15 15 15) = 15 * 15
    # 4 15 - petocas vezbe (45 45 45 45 45 + 15 15)         = 15 * 17
    """

    if num_of_15s == 3:
        return 1
    if num_of_15s == 6 or num_of_15s == 7:
        return 2
    if num_of_15s == 9:
        return 3
    if num_of_15s == 10 or num_of_15s == 11:
        return 3
    if num_of_15s == 13 or num_of_15s == 15:
        return 4
    if num_of_15s == 17:
        return 5


def sheet_name_to_raspored_name(sheet_name):
    raspored_names = {
        "ANI": "Animacija u inženjerstvu",
        "ARH": "Arhitektura",
        "BIO": "Biomedicinsko inženjerstvo",
        "CET": "Čiste energetske tehnologije",
        "DTE": "Digitalne tehnike, dizajn i produkcija u arhitekturi",
        "EET": "Energetika, elektronika i telekomunikacije",
        "GEO": "Geodezija i geoinformatika",
        "GI": "Grafičko inženjerstvo i dizajn",
        "GR": "Građevinarstvo",
        # postoje dva rasporeda na osnovu ovog sheet-a
        "IIM": "Inženjersko inženjerstvo i menadžment",
        "IIS": "Inženjerstvo informacionih sistema",
        "INOV": "Inženjerstvo inovacija",
        "INZ": "Informacioni inženjering",
        "INB": "Informaciona bezbednost",
        "ITV": "Inženjerstvo tretmana i zaštite voda",
        "IZS": "Inženjerstvo zaštite životne sredine i zaštite na radu",
        "MAS": "Mašinstvo",
        "MAT": "Matematika u tehnici",
        "MT": "Mehatronika",
        "MER": "Merenje i regulacija",
        "PLA": "Planiranje i upravljanje regionalnim razvojem",
        "PRI": "Primenjeno softversko inženjerstvo",
        "RAC": "Računarstvo i automatika",
        "SAO": "Saobraćaj",
        "SCE": "Scenska arhitektura",
        "SIT": "Softversko inženjerstvo i informacione tehnologije",
        "UPR": "Upravljanje rizikom od katastrofalnih događaja i požara",
        "VEI": "Veštačka inteligencija i mašinsko učenje",
        "OSSEOS": "OSS Elektrotehnika",
        "OSSSIT": "OSS Softverske informacione tehnologije",
        "MSSEMS": "MSS Elektrotehnika",
        "MSSMBA": "MSS Inženjerski menadžment MBA",
        "MSSPMS": "MSS Proizvodno mašinstvo",
        "OSSET": "",
        "OSSEET": "",
    }
    return raspored_names[sheet_name]
