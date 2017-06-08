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


"""
from __future__ import unicode_literals

from django.db import models


class AvailabalityRestriction(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_availability_restriction'
        managed = False


class Prescribability(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_virtual_product_pres_status'
        managed = False


class VMPNonAvailability(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_virtual_product_non_avail'
        managed = False


class ControlledDrugCategory(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_control_drug_category'
        managed = False


class TariffCategory(models.Model):
    cd = models.IntegerField(primary_key=True)
    desc = models.CharField(max_length=50)

    def __str__(self):
        return self.desc

    class Meta:
        db_table = 'dmd_lookup_dt_payment_category'
        managed = False


class DMDProduct(models.Model):
    '''
    '''
    dmdid = models.IntegerField(primary_key=True)
    bnf_code = models.CharField(max_length=15, null=True, db_index=True)
    vpid = models.IntegerField(primary_key=True)  # could become foreign key
    display_name = models.CharField(max_length=40)
    # requiring additional monitoring in accordance with the European
    # Medicines Agency Additional Monitoring Scheme
    ema = models.CharField(max_length=15)
    prescribability = models.ForeignKey(
        Prescribability, db_column='pres_statcd')
    availability_restrictions = models.ForeignKey(
        AvailabalityRestriction, db_column='avail_restrictcd')
    vmp_non_availability = models.ForeignKey(
        VMPNonAvailability, db_column='non_availcd')
    # 1 = VMP, 2 = AMP
    concept_class = models.IntegerField(primary_key=True)
    # 1 = Generic, 2 = brand, 3 = Mannufactured Generic
    product_type = models.IntegerField()
    # in the nurse prescribers' formulary?
    is_in_nurse_formulary = models.BooleanField(db_column='nurse_f')
    is_in_dentist_formulary = models.BooleanField(db_column='dent_f')
    # Product order number - Order number of product within Drug Tariff
    product_order_no = models.TextField(db_column='prod_order_no')
    # indicates AMPs listed in part XVIIIA of the Drug Tariff
    is_blacklisted = models.BooleanField(db_column='sched_1')
    # Indicates items that are part of the Selected List Scheme
    is_schedule_2 = models.BooleanField(db_column='sched_2')
    # This flag indicates where a prescriber will receive a fee for
    # administering an item. This is only applicable to NHS primary
    # medical services contractors.
    can_have_personal_administration_fee = models.BooleanField(db_column='padm')
    # Indicates items that can be prescribed in instalments on a FP10
    # MDA form.
    is_fp10 = models.BooleanField(db_column='fp10_mda')
    # Borderline substances: foodstuffs and toiletries which can be
    # prescribed
    is_borderline_substance = models.BooleanField(db_column='acbs')
    has_assorted_flavours = models.BooleanField(db_column='assort_flav')
    controlled_drug_category = models.ForeignKey(
        ControlledDrugCategory, db_column='catcd')
    tariff_category = models.ForeignKey(
        TariffCategory, db_column='tariff_category')
    is_imported = models.BooleanField(db_column='flag_imported')
    is_broken_bulk = models.BooleanField(db_column='flag_broken_bulk')
    is_non_bioequivalent = models.BooleanField(
        db_column='flag_non_bioequivalence')
    is_special_container = models.BooleanField(
        db_column='flag_special_containers')

    class Meta:
        db_table = 'dmd_product'
        managed = False

    def __str__(self):
        return self.display_name
