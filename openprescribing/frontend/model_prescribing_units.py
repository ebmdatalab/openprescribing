import json
import os
from django.conf import settings


def set_units(practice):

    list_total = practice.male_0_4 + practice.female_0_4 + \
        practice.male_5_14 + practice.female_5_14 + \
        practice.male_15_24 + practice.female_15_24 + \
        practice.male_25_34 + practice.female_25_34 + \
        practice.male_35_44 + practice.female_35_44 + \
        practice.male_45_54 + practice.female_45_54 + \
        practice.male_55_64 + practice.female_55_64 + \
        practice.male_65_74 + practice.female_65_74 + \
        practice.male_75_plus + practice.female_75_plus
    practice.total_list_size = list_total

    item_costs = {
        'male_0_4': 1.0,
        'female_0_4': 0.874764602225095,
        'male_5_14': 0.871655388261018,
        'female_5_14': 0.736837170135133,
        'male_15_24': 1.22586428186498,
        'female_15_24': 1.44903466533634,
        'male_25_34': 1.25432789273113,
        'female_25_34': 1.84193852699796,
        'male_35_44': 1.81674766893969,
        'female_35_44': 2.57229387381937,
        'male_45_54': 3.08974457158975,
        'female_45_54': 3.72488353721683,
        'male_55_64': 5.28280419664147,
        'female_55_64': 5.44244517326563,
        'male_65_74': 8.74186911115141,
        'female_65_74': 7.64083013196212,
        'male_75_plus': 11.3430752706509,
        'female_75_plus': 9.88935302232237
    }
    astro_pu_cost = 0
    for k in item_costs:
        astro_pu_cost += item_costs[k] * getattr(practice, k)
    practice.astro_pu_cost = astro_pu_cost

    item_weights = {
        'male_0_4': 5.20981299276732,
        'female_0_4': 4.57209109157611,
        'male_5_14': 2.78274827419795,
        'female_5_14': 2.49791988847988,
        'male_15_24': 2.54173833276,
        'female_15_24': 4.55423953314265,
        'male_25_34': 2.94877111448744,
        'female_25_34': 6.02048572645931,
        'male_35_44': 4.88518914434322,
        'female_35_44': 8.27380247373141,
        'male_45_54': 8.71276955913741,
        'female_45_54': 12.3262908574135,
        'male_55_64': 16.6039274295768,
        'female_55_64': 19.1280714382989,
        'male_65_74': 29.9412096036049,
        'female_65_74': 30.4100929796907,
        'male_75_plus': 44.9462923989395,
        'female_75_plus': 48.4846679987704
    }
    astro_pu_items = 0
    for k in item_weights:
        astro_pu_items += item_weights[k] * getattr(practice, k)
    practice.astro_pu_items = astro_pu_items

    star_pus = {}
    path = os.path.join(settings.SITE_ROOT, 'frontend', 'star_pu_weights.json')
    with open(path) as json_file:
        weights = json.load(json_file)
        for star_pu_name in weights:
            w = weights[star_pu_name]
            star_pus[star_pu_name] = \
                (w['0-4'][0] * float(practice.male_0_4)) + \
                (w['0-4'][1] * float(practice.female_0_4)) + \
                (w['5-14'][0] * float(practice.male_5_14)) + \
                (w['5-14'][1] * float(practice.female_5_14)) + \
                (w['15-24'][0] * float(practice.male_15_24)) + \
                (w['15-24'][1] * float(practice.female_15_24)) + \
                (w['25-34'][0] * float(practice.male_25_34)) + \
                (w['25-34'][1] * float(practice.female_25_34)) + \
                (w['35-44'][0] * float(practice.male_35_44)) + \
                (w['35-44'][1] * float(practice.female_35_44)) + \
                (w['45-54'][0] * float(practice.male_45_54)) + \
                (w['45-54'][1] * float(practice.female_45_54)) + \
                (w['55-64'][0] * float(practice.male_55_64)) + \
                (w['55-64'][1] * float(practice.female_55_64)) + \
                (w['65-74'][0] * float(practice.male_65_74)) + \
                (w['65-74'][1] * float(practice.female_65_74)) + \
                (w['75+'][0] * float(practice.male_75_plus)) + \
                (w['75+'][1] * float(practice.female_75_plus))
        practice.star_pu = star_pus

    return practice
