import cPickle
import json
import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from anymail.signals import EventType

from common.utils import nhs_titlecase
from dmd2.models import (
    VMP,
    AMP,
    VMPP,
    DtPaymentCategory,
    AvailabilityRestriction,
    VirtualProductPresStatus,
)
from frontend.managers import MeasureValueQuerySet
from frontend.validators import isAlphaNumeric
from frontend import model_prescribing_units


class Section(models.Model):
    bnf_id = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=200)
    number_str = models.CharField(max_length=12)
    bnf_chapter = models.IntegerField()
    bnf_section = models.IntegerField(null=True, blank=True)
    bnf_para = models.IntegerField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    def __unicode__(self):
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


class RegionalTeamManager(models.Manager):

    def active(self):
        return self.exclude(close_date__isnull=False).exclude(pct=None)


class RegionalTeam(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    open_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=400, null=True, blank=True)
    postcode = models.CharField(max_length=10, null=True, blank=True)

    objects = RegionalTeamManager()

    def __str__(self):
        return self.name

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)


class STP(models.Model):
    ons_code = models.CharField(max_length=9, primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)

    @property
    def code(self):
        return self.ons_code


class PCT(models.Model):
    '''
    PCTs or CCGs (depending on date).
    '''
    PCT_ORG_TYPES = (
        ('CCG', 'CCG'),
        ('PCT', 'PCT'),
        ('H', 'Hub'),
        ('Unknown', 'Unknown')
    )
    code = models.CharField(max_length=3, primary_key=True,
                            help_text='Primary care trust code')

    # These are NULLable, because not every PCT belongs to either a
    # RegionalTeam or an STP.  Specifically, we create PCT objects when
    # importing prescribing data if the PCT is not otherwise in our database.
    regional_team = models.ForeignKey(RegionalTeam, null=True)
    stp = models.ForeignKey(STP, null=True)

    ons_code = models.CharField(max_length=9, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    org_type = models.CharField(max_length=9, choices=PCT_ORG_TYPES,
                                default='Unknown')
    boundary = models.GeometryField(null=True, blank=True, srid=4326)
    centroid = models.PointField(null=True, blank=True)
    open_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=400, null=True, blank=True)
    postcode = models.CharField(max_length=10, null=True, blank=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name or ""

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)


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

    STATUS_RETIRED = 'B'
    STATUS_CLOSED = 'C'
    STATUS_DORMANT = 'D'

    STATUS_SETTINGS = (
        ('U', 'Unknown'),
        ('A', 'Active'),
        (STATUS_RETIRED, 'Retired'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_DORMANT, 'Dormant'),
        ('P', 'Proposed')
    )
    ccg = models.ForeignKey(PCT, null=True, blank=True)
    code = models.CharField(max_length=6, primary_key=True,
                            help_text='Practice code')
    name = models.CharField(max_length=200)
    address1 = models.CharField(max_length=200, null=True, blank=True)
    address2 = models.CharField(max_length=200, null=True, blank=True)
    address3 = models.CharField(max_length=200, null=True, blank=True)
    address4 = models.CharField(max_length=200, null=True, blank=True)
    address5 = models.CharField(max_length=200, null=True, blank=True)
    postcode = models.CharField(max_length=9, null=True, blank=True)
    location = models.PointField(null=True, blank=True)
    setting = models.IntegerField(choices=PRESCRIBING_SETTINGS,
                                  default=-1)
    objects = models.GeoManager()
    open_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    join_provider_date = models.DateField(null=True, blank=True)
    leave_provider_date = models.DateField(null=True, blank=True)
    status_code = models.CharField(max_length=1,
                                   choices=STATUS_SETTINGS,
                                   null=True, blank=True)
    ccg_change_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)

    def is_inactive(self):
        return self.status_code in (
            self.STATUS_RETIRED, self.STATUS_DORMANT, self.STATUS_CLOSED
        )

    def inactive_status_suffix(self):
        if self.is_inactive():
            return ' - {}'.format(self.get_status_code_display())
        else:
            return ''

    def address_pretty(self):
        address = self.address1 + ', '
        if self.address2:
            address += self.address2 + ', '
        if self.address3:
            address += self.address3 + ', '
        if self.address4:
            address += self.address4 + ', '
        if self.address5:
            address += self.address5 + ', '
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
        if self.address5:
            address += self.address5 + ', '
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


class PracticeStatistics(models.Model):
    '''
    Statistics for a practice in a particular month, including
    list sizes and derived values such as ASTRO-PUs and STAR-PUs.
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

    star_pu = JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self = model_prescribing_units.set_units(self)
        super(PracticeStatistics, self).save(*args, **kwargs)

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
    is_current = models.BooleanField(default=True)

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
    is_current = models.BooleanField(default=True)

    def __str__(self):
        return '%s: %s' % (self.bnf_code, self.name)

    def save(self, *args, **kwargs):
        self.is_generic = (self.bnf_code[-2:] == 'AA')
        super(Product, self).save(*args, **kwargs)

    class Meta:
        app_label = 'frontend'


class PresentationManager(models.Manager):
    def current(self):
        return self.filter(replaced_by__isnull=True)


class Presentation(models.Model):
    '''GP prescribing products. Import from BNF codes file from BSA.
    ADQs imported from BSA data.

    Where codes have changed or otherwise been mapped, the
    `replaced_by` field has a value.

    '''
    bnf_code = models.CharField(max_length=15, primary_key=True,
                                validators=[isAlphaNumeric])
    name = models.CharField(max_length=200)
    is_generic = models.NullBooleanField(default=None)
    is_current = models.BooleanField(default=True)
    replaced_by = models.ForeignKey('self', null=True, blank=True)

    # An ADQ is the assumed average maintenance dose per day for a
    # drug used for its main indication in adults.
    #
    # If a presentation's ADQ is "20mg", and its `quantity` field is
    # measured in 10 mg tablets, then the `adq_per_quantity` whould be
    # 2.  In other words, `adq_per_quantity` is a factor to apply to
    # `quantity`, to obtain an ADQ.
    #
    # See https://github.com/ebmdatalab/openprescribing/issues/934 for
    # more detail
    adq_per_quantity = models.FloatField(null=True, blank=True)

    # Usually `quantity` measures something that comes *in* a pack e.g. "number
    # of tablets" or "number of ml of liquid". (Note this is "pack" in the DM+D
    # sense were a bottle and pump are both "packs"). Occasionally though,
    # `quantity` measures the number of packs itself. This field is set by the
    # `set_quantity_means_pack` management command and should not be modified
    # by anything else, especially not by hand.
    quantity_means_pack = models.NullBooleanField(default=None)

    # The name of the corresponding product (or product pack) in dm+d.  This
    # tends to be more user-friendly than the names in the BNF.  See
    # set_dmd_names in import_dmd command for details of how this is set.
    dmd_name = models.CharField(max_length=255, null=True)

    objects = PresentationManager()

    def __str__(self):
        return '%s: %s' % (self.bnf_code, self.product_name)

    def save(self, *args, **kwargs):
        if len(self.bnf_code) > 10:
            code = self.bnf_code[9:11]
            is_generic = (code == 'AA')
        else:
            is_generic = None
        self.is_generic = is_generic
        super(Presentation, self).save(*args, **kwargs)

    @property
    def current_version(self):
        """BNF codes are replaced over time.

        Return the most recent version the code.
        """
        version = self
        next_version = self.replaced_by
        seen = []
        while next_version:
            if next_version in seen:
                break  # avoid loops
            else:
                seen.append(next_version)
                version = next_version
                next_version = version.replaced_by
        return version

    def tariff_categories(self):
        '''Return all tariff categories for this presentation.'''
        vmpps = VMPP.objects.filter(bnf_code=self.bnf_code)
        return DtPaymentCategory.objects.filter(dtinfo__vmpp__in=vmpps).distinct()

    def tariff_categories_descr(self):
        '''Return a description of the presentation's tariff category/ies.'''
        return ', '.join(tc.descr for tc in self.tariff_categories())

    def availability_restrictions(self):
        '''Return all availability restrictions for this presentation.'''
        amps = AMP.objects.filter(bnf_code=self.bnf_code)
        return AvailabilityRestriction.objects.filter(amp__in=amps).distinct()

    def availability_restrictions_descr(self):
        '''Return a description of the presentation's availabilty restriction/s.

        If any AMPs have "None" as their availability restriction, we
        consider that the presentation itself has no availability restriction.
        '''
        descrs = [ar.descr for ar in self.availability_restrictions()]
        if 'None' in descrs:
            return 'None'
        else:
            return ', '.join(descrs)

    def prescribability_statuses(self):
        '''Return all prescribability statuses for this presentation.
        '''
        vmps = VMP.objects.filter(bnf_code=self.bnf_code)
        return VirtualProductPresStatus.objects.filter(vmp__in=vmps).distinct()

    def prescribability_statuses_descr(self):
        '''Return a description of the presentation's prescribability status/es.'''
        return ', '.join(ps.descr for ps in self.prescribability_statuses())

    def dmd_info(self):
        '''Return dictionary of information about this presentation extracted
        from the dm+d data.'''

        info = {
            'tariff_categories': self.tariff_categories_descr(),
            'availability_restrictions': self.availability_restrictions_descr(),
            'prescribability_statuses': self.prescribability_statuses_descr(),
        }
        return {k: v for k, v in info.items() if v}

    @property
    def product_name(self):
        return self.dmd_name or self.name

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
    pct = models.ForeignKey(PCT, db_constraint=False, null=True)
    practice = models.ForeignKey(Practice, db_constraint=False, null=True)
    presentation_code = models.CharField(max_length=15,
                                         validators=[isAlphaNumeric])
    total_items = models.IntegerField()
    # XXX change this post-deploy; in fact we should not allow blanks
    net_cost = models.FloatField(blank=True, null=True)
    actual_cost = models.FloatField()
    quantity = models.FloatField()
    processing_date = models.DateField()

    class Meta:
        app_label = 'frontend'


class Measure(models.Model):
    # Some of these fields are documented in
    # https://github.com/ebmdatalab/openprescribing/wiki/Measure-definitions

    id = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    description = models.TextField()
    why_it_matters = models.TextField(null=True, blank=True)
    numerator_short = models.CharField(max_length=100, null=True, blank=True)
    tags = ArrayField(models.CharField(max_length=30), blank=True)
    tags_focus = ArrayField(
        models.CharField(max_length=30), null=True, blank=True,
        help_text=("Indicates that this measure is an aggregate made up of "
                   "all measures with the listed tags"))
    denominator_short = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    numerator_from = models.TextField()
    numerator_where = models.TextField()
    numerator_columns = models.TextField()
    denominator_from = models.TextField()
    denominator_where = models.TextField()
    denominator_columns = models.TextField()
    url = models.URLField(null=True, blank=True)
    is_percentage = models.NullBooleanField()
    is_cost_based = models.NullBooleanField()
    low_is_good = models.NullBooleanField()
    numerator_bnf_codes = ArrayField(models.CharField(max_length=15))
    numerator_bnf_codes_query = models.CharField(max_length=10000, null=True)
    numerator_is_list_of_bnf_codes = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'frontend'


class MeasureValue(models.Model):
    '''
    An instance of a measure for a particular organisation,
    on a particular date.
    If it's a measure for a CCG, the practice field will be null.
    Otherwise, it's a measure for a practice, and the pct field
    indicates the parent CCG, if it exists.
    '''
    measure = models.ForeignKey(Measure)
    regional_team = models.ForeignKey(RegionalTeam, null=True, blank=True)
    stp = models.ForeignKey(STP, null=True, blank=True)
    pct = models.ForeignKey(PCT, null=True, blank=True)
    practice = models.ForeignKey(Practice, null=True, blank=True)
    month = models.DateField()

    numerator = models.FloatField(null=True, blank=True)
    denominator = models.FloatField(null=True, blank=True)
    calc_value = models.FloatField(null=True, blank=True)

    percentile = models.FloatField(null=True, blank=True)

    # Cost savings if organisation had prescribed at set levels.
    # Only used with cost-based measures.
    cost_savings = JSONField(null=True, blank=True)

    class Meta:
        app_label = 'frontend'
        unique_together = (('measure', 'pct', 'practice', 'month'),)

    objects = MeasureValueQuerySet.as_manager()


class MeasureGlobal(models.Model):
    '''
    An instance of the global values for a measure,
    on a particular date.
    Percentile values may or may not be required. We
    include them as placeholders for now.
    '''
    measure = models.ForeignKey(Measure)
    month = models.DateField()

    numerator = models.FloatField(null=True, blank=True)
    denominator = models.FloatField(null=True, blank=True)
    calc_value = models.FloatField(null=True, blank=True)

    # Percentile values for practices.
    percentiles = JSONField(null=True, blank=True)
    cost_savings = JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.denominator is not None:
            self.denominator = float(self.denominator)
        if self.numerator is not None:
            self.numerator = float(self.numerator)
        if self.denominator:
            if self.numerator:
                self.calc_value = self.numerator / self.denominator
            else:
                self.calc_value = self.numerator
        else:
            self.value = None
        super(MeasureGlobal, self).save(*args, **kwargs)

    class Meta:
        app_label = 'frontend'
        unique_together = (('measure', 'month'),)


class TruncatingCharField(models.CharField):
    def get_prep_value(self, value):
        value = super(TruncatingCharField, self).get_prep_value(value)
        if value:
            return value[:self.max_length]
        return value


class SearchBookmark(models.Model):
    '''A bookmark for an individual analyse search made by a user.
    '''
    name = TruncatingCharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Bookmark: ' + self.name

    def topic(self):
        """Sentence snippet describing the bookmark
        """
        return self.name

    def dashboard_url(self):
        """The 'home page' for this bookmark

        """
        return "%s#%s" % (reverse('analyse'), self.url)


class OrgBookmark(models.Model):
    '''
    A bookmark for an organistion a user is interested in.

    If a bookmark for a CCG, the practice field will be null. If the practice
    field is set, it's a bookmark for a practice, and the pct field indicates
    the parent CCG, if it exists. If neither practice nor CCG is set then it's
    a bookmark for all of NHS England.

    (This is very much not ideal, but it has the benefit of consistency with
    the pattern already set in NCSOConcessionBookmark which should make
    refactoring easier, when it comes.)
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pct = models.ForeignKey(PCT, null=True, blank=True)
    practice = models.ForeignKey(Practice, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def dashboard_url(self, measure=None):
        """The 'home page' for a measure for this bookmark, or for all
        measures if none is specified
        """
        fragment = None
        if self.pct is not None and self.practice is None:
            if measure:
                view = 'measure_for_one_ccg'
                kwargs = {'measure': measure, 'entity_code': self.pct.code}
            else:
                view = 'measures_for_one_ccg'
                kwargs = {'ccg_code': self.pct.code}
        elif self.practice is not None:
            if measure:
                view = 'measure_for_one_practice'
                kwargs = {'measure': measure, 'entity_code': self.practice.code}
            else:
                view = 'measures_for_one_practice'
                kwargs = {'practice_code': self.practice.code}
        else:
            if measure:
                fragment = measure
            view = 'all_england'
            kwargs = {}

        url = reverse(view, kwargs=kwargs)
        if fragment:
            url = '{}#{}'.format(url, fragment)
        return url

    @property
    def name(self):
        if self.pct is not None and self.practice is None:
            return self.pct.cased_name
        elif self.practice is not None:
            return self.practice.cased_name
        else:
            return 'the NHS in England'

    def org_type(self):
        if self.pct is not None and self.practice is None:
            return 'CCG'
        elif self.practice is not None:
            return 'practice'
        else:
            return 'all_england'

    def topic(self):
        """Sentence snippet describing the bookmark
        """
        return "prescribing in %s" % self.name

    def get_absolute_url(self):
        return self.dashboard_url()

    def __unicode__(self):
        return 'Org Bookmark: ' + self.name


class NCSOConcessionBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pct = models.ForeignKey(PCT, null=True, blank=True)
    practice = models.ForeignKey(Practice, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    @property
    def entity(self):
        if self.pct is not None:
            return self.pct
        elif self.practice is not None:
            return self.practice
        else:
            # This is for all England
            return None

    @property
    def entity_type(self):
        if self.pct is not None:
            return 'CCG'
        elif self.practice is not None:
            return 'practice'
        else:
            return 'all_england'

    @property
    def entity_cased_name(self):
        if self.entity is None:
            return 'the NHS in England'
        else:
            return self.entity.cased_name

    @property
    def name(self):
        return 'NCSO concessions for {}'.format(self.entity_cased_name)

    def dashboard_url(self):
        if self.entity_type == 'CCG':
            kwargs = {'entity_code': self.entity.code}
            return reverse('spending_for_one_ccg', kwargs=kwargs)
        elif self.entity_type == 'practice':
            kwargs = {'entity_code': self.entity.code}
            return reverse('spending_for_one_practice', kwargs=kwargs)
        else:
            return reverse('spending_for_all_england')

    def topic(self):
        return self.name


class ImportLogManager(models.Manager):
    def latest_in_category(self, category):
        return self.filter(category=category).first()


class ImportLog(models.Model):
    '''
    Keep track of when things have been imported
    '''
    imported_at = models.DateTimeField(auto_now_add=True)
    current_at = models.DateField(db_index=True)
    filename = models.CharField(max_length=200)
    category = models.CharField(max_length=50, db_index=True)
    objects = ImportLogManager()

    class Meta:
        ordering = ["-current_at"]


def _makeKey():
    return uuid.uuid4().hex


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=32,
                           default=_makeKey,
                           unique=True)
    emails_received = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)

    def most_recent_bookmark(self):
        bookmarks = [
            bookmark for bookmark in [
                 self.user.orgbookmark_set.last(),
                 self.user.searchbookmark_set.last(),
                 self.user.ncsoconcessionbookmark_set.last(),
            ]
            if bookmark
        ]
        return sorted(bookmarks, key=lambda x: x.created_at)[-1]


class EmailMessageManager(models.Manager):
    def create_from_message(self, msg):
        user = User.objects.filter(email=msg.to[0])
        user = user and user[0] or None
        if 'message-id' not in msg.extra_headers:
            raise StandardError(
                "Messages stored as frontend.EmailMessage"
                "must have a message-id header")
        m = self.create(
            message_id=msg.extra_headers['message-id'],
            to=msg.to,
            subject=msg.subject,
            tags=msg.tags,
            user=user,
            message=msg
        )
        return m


class EmailMessage(models.Model):
    message_id = models.CharField(max_length=998, primary_key=True)
    pickled_message = models.BinaryField()
    to = ArrayField(
        models.CharField(max_length=254, db_index=True)
    )
    subject = models.CharField(max_length=200)
    tags = ArrayField(
        models.CharField(max_length=100, db_index=True),
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True)
    send_count = models.SmallIntegerField(default=0)
    objects = EmailMessageManager()

    @property
    def message(self):
        return cPickle.loads(str(self.pickled_message))

    @message.setter
    def message(self, value):
        self.pickled_message = cPickle.dumps(value)

    def send(self):
        self.message.send()
        self.send_count += 1
        self.save()

    def __unicode__(self):
        return self.subject


class MailLog(models.Model):
    EVENT_TYPE_CHOICES = [
        (value, value)
        for name, value in vars(EventType).iteritems()
        if not name.startswith('_')]
    # delievered, accepted (by mailgun), error, warn
    metadata = JSONField(null=True, blank=True)
    recipient = models.CharField(max_length=254, db_index=True)
    tags = ArrayField(
        models.CharField(max_length=100, db_index=True),
        null=True
    )
    reject_reason = models.CharField(max_length=15, null=True, blank=True)
    event_type = models.CharField(
        max_length=15,
        choices=EVENT_TYPE_CHOICES,
        db_index=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    message = models.ForeignKey(EmailMessage, null=True, db_constraint=False)

    def subject_from_metadata(self):
        subject = 'n/a'
        if 'subject' in self.metadata:
            subject = self.metadata['subject']
        elif 'message-headers' in self.metadata:
                headers = json.loads(self.metadata['message-headers'])
                subject_header = next(
                    (h for h in headers if h[0] == 'Subject'),
                    ['', 'n/a']
                )
                subject = subject_header[1]
        else:
            # e.g. "clicked" or "bounced" event_type
            try:
                if self.message:
                    subject = self.message.subject
            except EmailMessage.DoesNotExist:
                pass
        return subject


class GenericCodeMapping(models.Model):
    """A mapping between BNF codes that allows us to collapse clinically
    equivalent chemicals together.

    See https://github.com/ebmdatalab/price-per-dose/issues/11 for
    background.

    A `to_code` may end in `%`, which means it's a special case which
    should be treated as a stem against which to search for generics.

    """
    from_code = models.CharField(max_length=15, primary_key=True,
                                 validators=[isAlphaNumeric], db_index=True)
    to_code = models.CharField(max_length=15,
                               validators=[isAlphaNumeric], db_index=True)


class PPUSaving(models.Model):
    """A Price-per-unit Saving describes a possible saving for a CCG or a
    practice for an individual presentation.

    Records with a blank practice_id are for data at a CCG level;
    those with a practice_id are for data at a practice level.

    """
    date = models.DateField(db_index=True)
    # Sometimes we there are codes in prescribing data which are not
    # present in our presentations
    presentation = models.ForeignKey(
        Presentation, db_column='bnf_code', db_constraint=False)
    lowest_decile = models.FloatField()
    quantity = models.IntegerField()
    price_per_unit = models.FloatField()
    possible_savings = models.FloatField()
    formulation_swap = models.TextField(null=True, blank=True)
    pct = models.ForeignKey(PCT, null=True, blank=True, db_index=True)
    practice = models.ForeignKey(
        Practice, null=True, blank=True, db_index=True)


class TariffPrice(models.Model):
    date = models.DateField(db_index=True)
    vmpp = models.ForeignKey('dmd2.VMPP')
    # 1: Category A
    # 3: Category C
    # 11: Category M
    tariff_category = models.ForeignKey('dmd2.DtPaymentCategory')
    price_pence = models.IntegerField()

    class Meta:
        unique_together = ('date', 'vmpp')


class NCSOConcession(models.Model):
    date = models.DateField(db_index=True)
    vmpp = models.ForeignKey('dmd2.VMPP', null=True)
    drug = models.CharField(max_length=400)
    pack_size = models.CharField(max_length=40)
    price_pence = models.IntegerField()

    class Meta:
        unique_together = ('date', 'vmpp')

    class Manager(models.Manager):
        def unreconciled(self):
            return self.filter(vmpp__isnull=True)

    objects = Manager()

    @property
    def drug_and_pack_size(self):
        return u'{} {}'.format(self.drug, self.pack_size)
