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
        (0.874764602225095 * float(practice.female_0_4)) + \
        (0.871655388261018 * float(practice.male_5_14)) + \
        (0.736837170135133 * float(practice.female_5_14)) + \
        (1.22586428186498 * float(practice.male_15_24)) + \
        (1.44903466533634 * float(practice.female_15_24)) + \
        (1.25432789273113 * float(practice.male_25_34)) + \
        (1.84193852699796 * float(practice.female_25_34)) + \
        (1.81674766893969 * float(practice.male_35_44)) + \
        (2.57229387381937 * float(practice.female_35_44)) + \
        (3.08974457158975 * float(practice.male_45_54)) + \
        (3.72488353721683 * float(practice.female_45_54)) + \
        (5.28280419664147 * float(practice.male_55_64)) + \
        (5.44244517326563 * float(practice.female_55_64)) + \
        (8.74186911115141 * float(practice.male_65_74)) + \
        (7.64083013196212 * float(practice.female_65_74)) + \
        (11.3430752706509 * float(practice.male_75_plus)) + \
        (9.88935302232237 * float(practice.female_75_plus))
    practice.astro_pu_cost = astro_pu_cost

    astro_pu_items = (5.20981299276732 * float(practice.male_0_4)) + \
        (4.57209109157611 * float(practice.female_0_4)) + \
        (2.78274827419795 * float(practice.male_5_14)) + \
        (2.49791988847988 * float(practice.female_5_14)) + \
        (2.54173833276 * float(practice.male_15_24)) + \
        (4.55423953314265 * float(practice.female_15_24)) + \
        (2.94877111448744 * float(practice.male_25_34)) + \
        (6.02048572645931 * float(practice.female_25_34)) + \
        (4.88518914434322 * float(practice.male_35_44)) + \
        (8.27380247373141 * float(practice.female_35_44)) + \
        (8.71276955913741 * float(practice.male_45_54)) + \
        (12.3262908574135 * float(practice.female_45_54)) + \
        (16.6039274295768 * float(practice.male_55_64)) + \
        (19.1280714382989 * float(practice.female_55_64)) + \
        (29.9412096036049 * float(practice.male_65_74)) + \
        (30.4100929796907 * float(practice.female_65_74)) + \
        (44.9462923989395 * float(practice.male_75_plus)) + \
        (48.4846679987704 * float(practice.female_75_plus))
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
