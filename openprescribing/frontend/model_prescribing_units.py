import json


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

    astro_pu_cost = (1.0 * float(practice.male_0_4)) + \
        (0.9 * float(practice.female_0_4)) + \
        (0.9 * float(practice.male_5_14)) + \
        (0.7 * float(practice.female_5_14)) + \
        (1.2 * float(practice.male_15_24)) + \
        (1.4 * float(practice.female_15_24)) + \
        (1.3 * float(practice.male_25_34)) + \
        (1.8 * float(practice.female_25_34)) + \
        (1.8 * float(practice.male_35_44)) + \
        (2.6 * float(practice.female_35_44)) + \
        (3.1 * float(practice.male_45_54)) + \
        (3.7 * float(practice.female_45_54)) + \
        (5.3 * float(practice.male_55_64)) + \
        (5.4 * float(practice.female_55_64)) + \
        (8.7 * float(practice.male_65_74)) + \
        (7.6 * float(practice.female_65_74)) + \
        (11.3 * float(practice.male_75_plus)) + \
        (9.9 * float(practice.female_75_plus))
    practice.astro_pu_cost = astro_pu_cost

    astro_pu_items = (5.2 * float(practice.male_0_4)) + \
        (4.6 * float(practice.female_0_4)) + \
        (2.8 * float(practice.male_5_14)) + \
        (2.5 * float(practice.female_5_14)) + \
        (2.5 * float(practice.male_15_24)) + \
        (4.6 * float(practice.female_15_24)) + \
        (2.9 * float(practice.male_25_34)) + \
        (6.0 * float(practice.female_25_34)) + \
        (4.9 * float(practice.male_35_44)) + \
        (8.3 * float(practice.female_35_44)) + \
        (8.7 * float(practice.male_45_54)) + \
        (12.3 * float(practice.female_45_54)) + \
        (16.6 * float(practice.male_55_64)) + \
        (19.1 * float(practice.female_55_64)) + \
        (29.9 * float(practice.male_65_74)) + \
        (30.4 * float(practice.female_65_74)) + \
        (44.9 * float(practice.male_75_plus)) + \
        (48.5 * float(practice.female_75_plus))
    practice.astro_pu_items = astro_pu_items

    star_pus = {}
    with open("frontend/star_pu_weights.json") as json_file:
        weights = json.load(json_file)
        for star_pu_name in weights:
            w = weights[star_pu_name]
            star_pus[star_pu_name] = (w['0-4'][0] * float(practice.male_0_4)) + \
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
