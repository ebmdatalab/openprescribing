"""These models correspond with a subset of the tables whose schema is
implied by the raw D+MD XML.

There are no migrations for these models; the tables and their
contents are generated directly from raw XML files by the `import_dmd`
management command.

We use the `db_table` attribute to set table names to match the names
in the original XML.  This allows easier cross-referencing with the
Data Model and Implementation Guides published by the NHS BSA:

 * Data Model: docs/Data_Model_R2_v3.1_May_2015.pdf
 * Implementation: docs/dmd_Implemention_Guide_%28Primary_Care%29_v1.0.pdf

Note that many other tables are imported but not necessarily modelled
here. For some examples of the kinds of query that are possible, see:

https://github.com/ebmdatalab/price-per-dose/blob/master/snomed-bnf-mapping.ipynb

"""
from __future__ import unicode_literals

from django.db import models


class AvailabilityRestriction(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_availability_restriction'


class Prescribability(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_virtual_product_pres_status'


class VMPNonAvailability(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_virtual_product_non_avail'


class ControlledDrugCategory(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_control_drug_category'


class TariffCategory(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_dt_payment_category'


class DMDProduct(models.Model):
    '''A model that combines AMPs and VPMs to make mapping to legacy BNF
    codes easier, and to cache lookups on commonly-useful relations.

    '''
    dmdid = models.BigIntegerField(primary_key=True)
    bnf_code = models.CharField(max_length=15, null=True, db_index=True)
    vpid = models.BigIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=40)
    full_name = models.TextField(null=True)
    # requiring additional monitoring in accordance with the European
    # Medicines Agency Additional Monitoring Scheme
    ema = models.CharField(max_length=15, null=True)
    prescribability = models.ForeignKey(
        Prescribability, db_column='pres_statcd', null=True)
    availability_restrictions = models.ForeignKey(
        AvailabilityRestriction, db_column='avail_restrictcd', null=True)
    vmp_non_availability = models.ForeignKey(
        VMPNonAvailability, db_column='non_availcd', null=True)
    # 1 = VMP, 2 = AMP
    concept_class = models.IntegerField(db_index=True, null=True)
    # 1 = Generic, 2 = brand, 3 = Mannufactured Generic
    product_type = models.IntegerField(null=True)
    # in the nurse prescribers' formulary?
    is_in_nurse_formulary = models.NullBooleanField(db_column='nurse_f')
    is_in_dentist_formulary = models.NullBooleanField(db_column='dent_f')
    # Product order number - Order number of product within Drug Tariff
    product_order_no = models.TextField(db_column='prod_order_no', null=True)
    # indicates AMPs listed in part XVIIIA of the Drug Tariff
    is_blacklisted = models.NullBooleanField(db_column='sched_1')
    # Indicates items that are part of the Selected List Scheme
    is_schedule_2 = models.NullBooleanField(db_column='sched_2')
    # This flag indicates where a prescriber will receive a fee for
    # administering an item. This is only applicable to NHS primary
    # medical services contractors.
    can_have_personal_administration_fee = models.NullBooleanField(
        db_column='padm')
    # Indicates items that can be prescribed in instalments on a FP10
    # MDA form.
    is_fp10 = models.NullBooleanField(db_column='fp10_mda')
    # Borderline substances: foodstuffs and toiletries which can be
    # prescribed
    is_borderline_substance = models.NullBooleanField(db_column='acbs')
    has_assorted_flavours = models.NullBooleanField(db_column='assort_flav')
    controlled_drug_category = models.ForeignKey(
        ControlledDrugCategory, db_column='catcd', null=True)
    tariff_category = models.ForeignKey(
        TariffCategory, db_column='tariff_category', null=True)
    is_imported = models.NullBooleanField(db_column='flag_imported')
    is_broken_bulk = models.NullBooleanField(db_column='flag_broken_bulk')
    is_non_bioequivalent = models.NullBooleanField(
        db_column='flag_non_bioequivalence')
    is_special_container = models.NullBooleanField(
        db_column='flag_special_containers')

    class Meta:
        db_table = 'dmd_product'

    def __str__(self):
        return self.full_name

    @property
    def amps(self):
        return DMDProduct.objects.filter(
            vpid=self.dmdid).filter(concept_class=2)

    @property
    def vmp(self):
        if self.concept_class == 1:
            raise DMDProduct.DoesNotExist("You can't find a VMP of a VMP")
        vmp = DMDProduct.objects.filter(
            dmdid=self.vpid, concept_class=1).exclude(vpid=self.dmdid)
        assert len(vmp) < 2, "An AMP should only ever have one VMP"
        return vmp[0]
