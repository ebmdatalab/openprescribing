from django.contrib.gis.db import models
from validators import isAlphaNumeric


class Section(models.Model):
    bnf_id = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=200)
    number_str = models.CharField(max_length=12)
    bnf_chapter = models.IntegerField()
    bnf_section = models.IntegerField(null=True, blank=True)
    bnf_para = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.number_str = self.get_number_str(self.bnf_id)
        super(Section, self).save(*args, **kwargs)

    def get_number_str(self, id):
        s1 = self.strip_zeros(id[:2])
        s2 = self.strip_zeros(id[2:4])
        s3 = self.strip_zeros(id[4:6])
        s4 = self.strip_zeros(id[6:8])
        number = str(s1)
        if s2:
            number += '.%s' % s2
        if s3:
            number += '.%s' % s3
        if s4:
            number += '.%s' % s4
        return number

    def strip_zeros(self, str):
        if not str or str == '0' or str == '00':
            return None
        if len(str) > 1 and str[0] == '0':
            str = str[1:]
        return int(str)

    class Meta:
        ordering = ["bnf_id"]


class SHA(models.Model):
    '''
    SHAs or Area Teams (depending on date).
    '''
    code = models.CharField(max_length=3, primary_key=True,
                            help_text='Strategic health authority code')
    ons_code = models.CharField(max_length=9, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    boundary = models.MultiPolygonField(null=True, blank=True)

    objects = models.GeoManager()


class PCT(models.Model):
    '''
    PCTs or CCGs (depending on date).
    '''
    PCT_ORG_TYPES = (
        ('CCG', 'CCG'),
        ('PCT', 'PCT'),
        ('Unknown', 'Unknown')
    )
    code = models.CharField(max_length=3, primary_key=True,
                            help_text='Primary care trust code')
    ons_code = models.CharField(max_length=9, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    org_type = models.CharField(max_length=9, choices=PCT_ORG_TYPES,
                                default='Unknown')
    boundary = models.GeometryField(null=True, blank=True)
    managing_group = models.ForeignKey(SHA, null=True, blank=True)

    objects = models.GeoManager()


class Practice(models.Model):
    '''
    GP practices. HSCIC practice status is from:
    http://systems.hscic.gov.uk/data/ods/datadownloads/gppractice/index_html
    '''
    PRESCRIBING_SETTINGS = (
        (-1, 'Unknown'),
        (0, 'Other'),
        (1, 'WIC Practice'),
        (2, 'OOH Practice'),
        (3, 'WIC + OOH Practice'),
        (4, 'GP Practice'),
        (8, 'Public Health Service'),
        (9, 'Community Health Service'),
        (10, 'Hospital Service'),
        (11, 'Optometry Service'),
        (12, 'Urgent & Emergency Care'),
        (13, 'Hospice'),
        (14, 'Care Home / Nursing Home'),
        (15, 'Border Force'),
        (16, 'Young Offender Institution'),
        (17, 'Secure Training Centre'),
        (18, "Secure Children's Home"),
        (19, "Immigration Removal Centre"),
        (20, "Court"),
        (21, "Police Custody"),
        (22, "Sexual Assault Referral Centre (SARC)"),
        (24, "Other - Justice Estate"),
        (25, "Prison")
    )
    ccg = models.ForeignKey(PCT, null=True, blank=True)
    area_team = models.ForeignKey(SHA, null=True, blank=True)
    code = models.CharField(max_length=6, primary_key=True,
                            help_text='Practice code')
    name = models.CharField(max_length=200)
    address1 = models.CharField(max_length=200, null=True, blank=True)
    address2 = models.CharField(max_length=200, null=True, blank=True)
    address3 = models.CharField(max_length=200, null=True, blank=True)
    address4 = models.CharField(max_length=200, null=True, blank=True)
    postcode = models.CharField(max_length=9, null=True, blank=True)
    location = models.PointField(null=True, blank=True)
    setting = models.IntegerField(choices=PRESCRIBING_SETTINGS,
                                  default=-1)
    objects = models.GeoManager()

    def __str__(self):
        return self.name

    def address_pretty(self):
        address = self.address1 + ', '
        if self.address2:
            address += self.address2 + ', '
        if self.address3:
            address += self.address3 + ', '
        if self.address4:
            address += self.address4 + ', '
        address += self.postcode
        return address

    def address_pretty_minus_firstline(self):
        address = ''
        if self.address2:
            address += self.address2 + ', '
        if self.address3:
            address += self.address3 + ', '
        if self.address4:
            address += self.address4 + ', '
        address += self.postcode
        return address

    class Meta:
        app_label = 'frontend'


class PracticeIsDispensing(models.Model):
    '''
    Dispensing status, from
    https://www.report.ppa.org.uk/ActProd1/getfolderitems.do?volume=actprod&userid=ciruser&password=foicir
    '''
    practice = models.ForeignKey(Practice)
    date = models.DateField()

    class Meta:
        app_label = 'frontend'
        unique_together = ("practice", "date")


class PracticeList(models.Model):
    '''
    List size categories from NHS BSA.
    '''
    practice = models.ForeignKey(Practice)
    pct = models.ForeignKey(PCT, null=True, blank=True)
    date = models.DateField()
    male_0_4 = models.IntegerField()
    female_0_4 = models.IntegerField()
    male_5_14 = models.IntegerField()
    female_5_14 = models.IntegerField()
    male_15_24 = models.IntegerField()
    female_15_24 = models.IntegerField()
    male_25_34 = models.IntegerField()
    female_25_34 = models.IntegerField()
    male_35_44 = models.IntegerField()
    female_35_44 = models.IntegerField()
    male_45_54 = models.IntegerField()
    female_45_54 = models.IntegerField()
    male_55_64 = models.IntegerField()
    female_55_64 = models.IntegerField()
    male_65_74 = models.IntegerField()
    female_65_74 = models.IntegerField()
    male_75_plus = models.IntegerField()
    female_75_plus = models.IntegerField()
    total_list_size = models.IntegerField()
    astro_pu_cost = models.FloatField()
    astro_pu_items = models.FloatField()
    star_pu_oral_antibac_items = models.FloatField()

    def save(self, *args, **kwargs):
        list_total = self.male_0_4 + self.female_0_4 + \
            self.male_5_14 + self.female_5_14 + \
            self.male_15_24 + self.female_15_24 + \
            self.male_25_34 + self.female_25_34 + \
            self.male_35_44 + self.female_35_44 + \
            self.male_45_54 + self.female_45_54 + \
            self.male_55_64 + self.female_55_64 + \
            self.male_65_74 + self.female_65_74 + \
            self.male_75_plus + self.female_75_plus
        self.total_list_size = list_total

        astro_pu_cost = (1.0 * float(self.male_0_4)) + \
            (0.9 * float(self.female_0_4)) + \
            (0.9 * float(self.male_5_14)) + \
            (0.7 * float(self.female_5_14)) + \
            (1.2 * float(self.male_15_24)) + \
            (1.4 * float(self.female_15_24)) + \
            (1.3 * float(self.male_25_34)) + \
            (1.8 * float(self.female_25_34)) + \
            (1.8 * float(self.male_35_44)) + \
            (2.6 * float(self.female_35_44)) + \
            (3.1 * float(self.male_45_54)) + \
            (3.7 * float(self.female_45_54)) + \
            (5.3 * float(self.male_55_64)) + \
            (5.4 * float(self.female_55_64)) + \
            (8.7 * float(self.male_65_74)) + \
            (7.6 * float(self.female_65_74)) + \
            (11.3 * float(self.male_75_plus)) + \
            (9.9 * float(self.female_75_plus))
        self.astro_pu_cost = astro_pu_cost

        astro_pu_items = (5.2 * float(self.male_0_4)) + \
            (4.6 * float(self.female_0_4)) + \
            (2.8 * float(self.male_5_14)) + \
            (2.5 * float(self.female_5_14)) + \
            (2.5 * float(self.male_15_24)) + \
            (4.6 * float(self.female_15_24)) + \
            (2.9 * float(self.male_25_34)) + \
            (6.0 * float(self.female_25_34)) + \
            (4.9 * float(self.male_35_44)) + \
            (8.3 * float(self.female_35_44)) + \
            (8.7 * float(self.male_45_54)) + \
            (12.3 * float(self.female_45_54)) + \
            (16.6 * float(self.male_55_64)) + \
            (19.1 * float(self.female_55_64)) + \
            (29.9 * float(self.male_65_74)) + \
            (30.4 * float(self.female_65_74)) + \
            (44.9 * float(self.male_75_plus)) + \
            (48.5 * float(self.female_75_plus))
        self.astro_pu_items = astro_pu_items

        star_pu_oral_antibac_items = (0.8 * float(self.male_0_4)) + \
            (0.8 * float(self.female_0_4)) + \
            (0.3 * float(self.male_5_14)) + \
            (0.4 * float(self.female_5_14)) + \
            (0.3 * float(self.male_15_24)) + \
            (0.6 * float(self.female_15_24)) + \
            (0.2 * float(self.male_25_34)) + \
            (0.6 * float(self.female_25_34)) + \
            (0.3 * float(self.male_35_44)) + \
            (0.6 * float(self.female_35_44)) + \
            (0.3 * float(self.male_45_54)) + \
            (0.6 * float(self.female_45_54)) + \
            (0.4 * float(self.male_55_64)) + \
            (0.7 * float(self.female_55_64)) + \
            (0.7 * float(self.male_65_74)) + \
            (1.0 * float(self.female_65_74)) + \
            (1.0 * float(self.male_75_plus)) + \
            (1.3 * float(self.female_75_plus))
        self.star_pu_oral_antibac_items = star_pu_oral_antibac_items

        super(PracticeList, self).save(*args, **kwargs)

    class Meta:
        app_label = 'frontend'


class QOFPrevalence(models.Model):
    '''
    TODO: Handle denormalization?
    '''
    pct = models.ForeignKey(PCT, null=True, blank=True)
    practice = models.ForeignKey(Practice, null=True, blank=True)
    start_year = models.IntegerField()
    indicator_group = models.CharField(max_length=10)
    register_description = models.CharField(max_length=100)
    disease_register_size = models.IntegerField()


class Chemical(models.Model):
    '''
    GP prescribing chemical substances (aka chemicals)
    TODO: Add 'date added' field, populate from data file.
    '''
    bnf_code = models.CharField(max_length=9, primary_key=True,
                                validators=[isAlphaNumeric])
    chem_name = models.CharField(max_length=200)

    def __str__(self):
        return '%s: %s' % (self.bnf_code, self.chem_name)

    def bnf_section(self):
        code = self.bnf_code
        section = Section.objects.get(bnf_chapter=int(code[:2]),
                                      bnf_section=int(code[2:4]),
                                      bnf_para=None)
        return "%s: %s" % (section.number_str, section.name)

    class Meta:
        app_label = 'frontend'
        unique_together = (('bnf_code', 'chem_name'),)


class Product(models.Model):
    '''
    GP prescribing products. Import from BNF codes file from BSA.
    '''
    bnf_code = models.CharField(max_length=11, primary_key=True,
                                validators=[isAlphaNumeric])
    name = models.CharField(max_length=200)
    is_generic = models.BooleanField()

    def __str__(self):
        return '%s: %s' % (self.bnf_code, self.name)

    def save(self, *args, **kwargs):
        self.is_generic = (self.bnf_code[-2:] == 'AA')
        super(Product, self).save(*args, **kwargs)

    class Meta:
        app_label = 'frontend'


class Presentation(models.Model):
    '''
    GP prescribing products. Import from BNF codes file from BSA.
    '''
    bnf_code = models.CharField(max_length=15, primary_key=True,
                                validators=[isAlphaNumeric])
    name = models.CharField(max_length=200)
    is_generic = models.NullBooleanField(default=None)

    def __str__(self):
        return '%s: %s' % (self.bnf_code, self.name)

    def save(self, *args, **kwargs):
        if len(self.bnf_code) > 10:
            code = self.bnf_code[9:11]
            is_generic = (code == 'AA')
        else:
            is_generic = None
        self.is_generic = is_generic
        super(Presentation, self).save(*args, **kwargs)

    class Meta:
        app_label = 'frontend'


class Prescription(models.Model):
    '''
    Prescription items
    Characters
    -- 1 & 2 show the BNF Chapter,
    -- 3 & 4 show the BNF Section,
    -- 5 & 6 show the BNF paragraph,
    -- 7 shows the BNF sub-paragraph and
    -- 8 & 9 show the chemical substance
    -- 10 & 11 show the Product
    -- 12 & 13 show the Strength and Formulation
    -- 14 & 15 show the equivalent generic code (always used)
    '''
    sha = models.ForeignKey(SHA)
    pct = models.ForeignKey(PCT)
    practice = models.ForeignKey(Practice)
    chemical = models.ForeignKey(Chemical)
    presentation_code = models.CharField(max_length=15, db_index=True,
                                         validators=[isAlphaNumeric])
    presentation_name = models.CharField(max_length=1000)
    total_items = models.IntegerField()
    net_cost = models.FloatField()
    actual_cost = models.FloatField()
    quantity = models.FloatField()
    processing_date = models.DateField(db_index=True)
    price_per_unit = models.FloatField()

    class Meta:
        app_label = 'frontend'
