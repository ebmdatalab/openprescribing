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
    ons_code = models.CharField(max_length=9, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    org_type = models.CharField(max_length=9, choices=PCT_ORG_TYPES,
                                default='Unknown')
    boundary = models.GeometryField(null=True, blank=True)
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
    STATUS_SETTINGS = (
        ('U', 'Unknown'),
        ('A', 'Active'),
        ('B', 'Retired'),
        ('C', 'Closed'),
        ('D', 'Dormant'),
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

    def __str__(self):
        return self.name

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)

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
    active_quantity = models.FloatField(null=True, blank=True)
    adq = models.FloatField(null=True, blank=True)
    adq_unit = models.CharField(max_length=10, null=True, blank=True)
    is_current = models.BooleanField(default=True)
    percent_of_adq = models.FloatField(null=True, blank=True)
    replaced_by = models.ForeignKey('self', null=True, blank=True)

    objects = PresentationManager()

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
    actual_cost = models.FloatField()
    quantity = models.FloatField()
    processing_date = models.DateField()

    class Meta:
        app_label = 'frontend'


class Measure(models.Model):
    id = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    description = models.TextField()
    why_it_matters = models.TextField(null=True, blank=True)
    numerator_short = models.CharField(max_length=100, null=True, blank=True)

    denominator_short = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    is_percentage = models.NullBooleanField()
    is_cost_based = models.NullBooleanField()
    low_is_good = models.NullBooleanField()

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
    pct = models.ForeignKey(PCT, null=True, blank=True)
    practice = models.ForeignKey(Practice, null=True, blank=True)
    month = models.DateField()

    numerator = models.FloatField(null=True, blank=True)
    denominator = models.FloatField(null=True, blank=True)
    calc_value = models.FloatField(null=True, blank=True)

    # Optionally store the raw values, where appropriate.
    # Cost and quantity are used for calculating cost savings.
    num_items = models.IntegerField(null=True, blank=True)
    denom_items = models.IntegerField(null=True, blank=True)
    num_cost = models.FloatField(null=True, blank=True)
    denom_cost = models.FloatField(null=True, blank=True)
    num_quantity = models.FloatField(null=True, blank=True)
    denom_quantity = models.FloatField(null=True, blank=True)

    percentile = models.FloatField(null=True, blank=True)

    # Cost savings if organisation had prescribed at set levels.
    # Only used with cost-based measures.
    cost_savings = JSONField(null=True, blank=True)

    class Meta:
        app_label = 'frontend'
        unique_together = (('measure', 'pct', 'practice', 'month'),)


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

    # Optionally store the raw values, where appropriate.
    # Cost and quantity are used for calculating cost savings.
    num_items = models.IntegerField(null=True, blank=True)
    denom_items = models.IntegerField(null=True, blank=True)
    num_cost = models.FloatField(null=True, blank=True)
    denom_cost = models.FloatField(null=True, blank=True)
    num_quantity = models.FloatField(null=True, blank=True)
    denom_quantity = models.FloatField(null=True, blank=True)
    cost_per_num = models.FloatField(null=True, blank=True)
    cost_per_denom = models.FloatField(null=True, blank=True)

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

    If a bookmark for a CCG, the practice field will be null.
    Otherwise, it's a bookmark for a practice, and the pct field
    indicates the parent CCG, if it exists.
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pct = models.ForeignKey(PCT, null=True, blank=True)
    practice = models.ForeignKey(Practice, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def dashboard_url(self):
        """The 'home page' for this bookmark

        """
        if self.practice is None:
            return reverse(
                'measures_for_one_ccg',
                kwargs={'ccg_code': self.pct.code})
        else:
            return reverse(
                'measures_for_one_practice',
                kwargs={'code': self.practice.code})

    @property
    def name(self):
        if self.practice is None:
            return self.pct.cased_name
        else:
            return self.practice.cased_name

    def org_type(self):
        if self.practice is None:
            return 'CCG'
        else:
            return 'practice'

    def topic(self):
        """Sentence snippet describing the bookmark
        """
        return "prescribing in %s" % self.name

    def get_absolute_url(self):
        return self.dashboard_url()

    def __unicode__(self):
        return 'Org Bookmark: ' + self.name


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
        org_bookmark = self.user.orgbookmark_set.last()
        search_bookmark = self.user.searchbookmark_set.last()
        bookmarks = [x for x in [org_bookmark, search_bookmark] if x]
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
            # likely to be "clicked" event
            try:
                subject = self.message.subject
            except EmailMessage.DoesNotExist:
                pass
        return subject
