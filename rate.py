import translations as tr
import artifacts as art
import re

from fuzzywuzzy import fuzz, process
from unidecode import unidecode

reg = re.compile(r'\d+(?:[.,]\d+)?')
bad_reg = re.compile(r'\d+/1000$')
hp_reg = re.compile(r'\d[.,]\d{3}')
lvl_reg = re.compile(r'^\+\d\d?$')
bad_lvl_reg_1 = re.compile(r'^\+?\d\d?$')
bad_lvl_reg_2 = re.compile(r'^\d{4}\d*$')

# Data processing
def parse(text, lang=tr.en(), lang2=art.en()):
    stat = None
    results = []
    level = None
    type = None
    set = None
    prev = None
    del_prev = True

    # Prepare dictionary
    elements = [lang.anemo, lang.elec, lang.pyro, lang.hydro, lang.cryo, lang.geo, lang.dend]
    choices = elements + [lang.hp, lang.heal, lang.df, lang.er, lang.em, lang.atk, lang.cd, lang.cr, lang.phys]
    choices = {unidecode(choice).lower(): choice for choice in choices}
    
    # Additional dictionary for artifact sets & type
    types = lang2.types
    types = {unidecode(x).lower(): x for x in types}
    sets = lang2.sets
    sets = {unidecode(x).lower(): x for x in sets}

    for line in text.splitlines():
        if not line or len(line.replace(' ','')) <= 1:
            continue

        if del_prev:
            prev = None
        del_prev = True

        # Basic cleaning
        for k,v in lang.replace.items():
            line = line.replace(k,v)
            
        line = unidecode(line).lower()
        line = line.replace(':','').replace('-','').replace('0/0','%')
        if line.replace(' ','') in lang.ignore or bad_reg.search(line.replace(' ','')):
            continue
        if  fuzz.partial_ratio(line, unidecode(lang.piece_set).lower()) > 80 and len(line) > 4:
            break

        # Search for level (ex. +16)
        if level == None or (len(results) == 1 and not stat):
            value = lvl_reg.search(line.replace(' ',''))
            if value:
                print('1', line)
                level = int(value[0].replace('+',''))
                continue

        # Search for HP (4,780)
        value = hp_reg.search(line.replace(' ',''))
        if value:
            print('2', line)
            value = int(value[0].replace(',','').replace('.',''))
            results += [[lang.hp, value]]
            stat = None
            continue
            
        # Search for type (ex. Goblet)
        # Compare to full dictionary (get best match + confidence)
        if type == None and len(line.replace(' ','')) > 3+2:
            extract = process.extractOne(line, list(types))
            
            # If the best match has high conf
            if (extract[1] > 80):
                type = types[extract[0]]
                continue
                
        # Search for type (ex. Goblet)
        # Compare to full dictionary (get best match + confidence)
        if set == None and len(line.replace(' ','')) > 3+2:
            extract = process.extractOne(line, list(sets))
            
            # If the best match has high conf
            if (extract[1] > 80):
                print('0', extract[0])
                set = sets[extract[0]]
                continue
        
        # Search for substats & mainstat
        # Compare to full dictionary (get best match + confidence)
        extract = process.extractOne(line, list(choices))
        # If low confidence, retry with another scorer
        if extract[1] <= 80:
            extract = process.extractOne(line, list(choices), scorer=fuzz.partial_ratio)

        # If conf is high
        if (extract[1] > 80) or stat:
            print('3', line)
            if (extract[1] > 80):
                stat = choices[extract[0]]
            value = reg.findall(line.replace(' ','').replace(',','.'))
            if not value:
                if not prev:
                    continue
                print('4', prev)
                value = prev
            value = max(value, key=len)
            if len(value) < 2:
                continue
            if line.find('%', line.find(value)) != -1 and '.' not in value:
                value = value[:-1] + '.' + value[-1]
            if '.' in value:
                value = float(value)
                stat += '%'
            else:
                value = int(value)
            results += [[stat, value]]
            stat = None 
            if len(results) == 6:
                break
            continue

        # If conf is low, do special bad cases
        value = bad_lvl_reg_1.search(line.replace(' ','')) or bad_lvl_reg_2.search(line.replace(' ','').replace('+',''))
        if not value:
            line = line.replace(',','')
            prev = reg.findall(line.replace(' ',''))
            del_prev = False

    print("\n", type, level, set, results, "\n")
    return type, level, set, results

def validate(value, max_stat, percent):
    while value > max_stat * 1.05:
        value = str(value)
        removed = False
        for i in reversed(range(1, len(value))):
            if value[i] == value[i-1]:
                value = value[:i-1] + value[i:]
                removed = True
                break
        if not removed:
            if percent:
                pos = value.find('.')
                value = value[:pos-1] + value[pos:]
            else:
                value = value[:-1]
        value = float(value) if percent else int(value)
    if int(value) == 1:
        value += 10
    return value

def score(level, results, options={}, lang=tr.en()):
    # Weight = max potential at the level
    # Score  = absolute artifact value
    # Score% = art value relative to max potential
    main = True
    main_score = 0.0
    sub_score = 0.0
    sub_weight = 0
    main_weight = 3 + level / 4

    elements = [lang.anemo, lang.elec, lang.pyro, lang.hydro, lang.cryo, lang.geo, lang.dend]

    min_mains = {lang.hp: 717.0, lang.atk: 47.0, f'{lang.atk}%': 7.0, f'{lang.er}%': 7.8, lang.em: 28.0,
                 f'{lang.phys}%': 8.7, f'{lang.cr}%': 4.7, f'{lang.cd}%': 9.3, f'{lang.elem}%': 7.0,
                 f'{lang.hp}%': 7.0, f'{lang.df}%': 8.7, f'{lang.heal}%': 5.4}
    max_mains = {lang.hp: 4780, lang.atk: 311.0, f'{lang.atk}%': 46.6, f'{lang.er}%': 51.8, lang.em: 187.0,
                 f'{lang.phys}%': 58.3, f'{lang.cr}%': 31.1, f'{lang.cd}%': 62.2, f'{lang.elem}%': 46.6,
                 f'{lang.hp}%': 46.6, f'{lang.df}%': 58.3, f'{lang.heal}%': 35.9}
    max_subs = {lang.atk: 19.0, lang.em: 23.0, f'{lang.er}%': 6.5, f'{lang.atk}%': 5.8,
                f'{lang.cr}%': 3.9, f'{lang.cd}%': 7.8, lang.df: 23.0, lang.hp: 299.0, f'{lang.df}%': 7.3, f'{lang.hp}%': 5.8}
    weights = {lang.hp: 0, lang.atk: 0.5, f'{lang.atk}%': 1, f'{lang.er}%': 0.5, lang.em: 0.5,
               f'{lang.phys}%': 1, f'{lang.cr}%': 1, f'{lang.cd}%': 1, f'{lang.elem}%': 1,
               f'{lang.hp}%': 0, f'{lang.df}%': 0, lang.df: 0, f'{lang.heal}%': 0}

    # Replaces weights with options
    weights = {**weights, **options}

    for result in results:
        stat, value = result
        key = stat if stat[:-1] not in elements else f'{lang.elem}%'
        if main:
            main = False
            max_main = max_mains[key] - (max_mains[key] - min_mains[key]) * (1 - level / 20.0)
            value = validate(value, max_main, '%' in key)
            main_score = value / max_main * weights[key] * main_weight
            if key in [lang.atk, lang.hp]:
                main_weight *= weights[key]
                
            count = 0
            for k,v in sorted(weights.items(), reverse=True, key=lambda item: item[1]):
                if k == key or k not in max_subs:
                    continue
                if count == 0:
                    sub_weight += v * (1 + level / 4)
                else:
                    sub_weight += v
                count += 1
                if count == 4:
                    break
        else:
            value = validate(value, max_subs[key] * 6, '%' in key)
            sub_score += value / max_subs[key] * weights[key]
        result[1] = value

    # Measure total score in terms of combined max potential
    total_score = main_score + sub_score
    total_weight = main_weight + sub_weight
    total_rel = total_score / total_weight * 100 if total_weight > 0 else 100
    
    # Only useful for 4* and below. Always 100 for 5*
    main_rel = main_score / main_weight * 100 if main_weight > 0 else 100
    main_rel = 100 if main_rel > 99 else main_rel
    
    # Compare score to max
    sub_rel = sub_score / sub_weight * 100 if sub_weight > 0 else 100
    
    print(f"Total: {total_score:.2f} {total_rel:.2f}% \n" +
        f"  Main: {main_score:.2f}/{main_weight}={main_rel:.2f}% \n" +
        f"  Sub: {sub_score:.2f}/{sub_weight}={sub_rel:.2f}% \n")
        
    return (total_score, total_rel), (main_score, main_rel), (sub_score, sub_rel)
 