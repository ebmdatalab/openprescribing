from django.db import models


class VTM(models.Model):
    vtmid = models.IntegerField(
        primary_key=True,
        help_text="VTM identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    nm = models.CharField(
        max_length=255,
        help_text="VTM Name",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="VTM Abbreviated name",
    )
    vtmidprev = models.IntegerField(
        null=True,
        help_text="Previous VTM identifier",
    )
    vtmiddt = models.DateField(
        null=True,
        help_text="VTM Identifier date",
    )


class VMP(models.Model):
    vpid = models.IntegerField(
        primary_key=True,
        help_text="VMP identifier",
    )
    vpiddt = models.DateField(
        null=True,
        help_text="Date VMP identifier became Valid",
    )
    vpidprev = models.IntegerField(
        null=True,
        help_text="Previous product identifier",
    )
    vtmid = models.ForeignKey(
        to="VTM",
        on_delete=models.CASCADE,
        null=True,
        help_text="VTM identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    nm = models.CharField(
        max_length=255,
        help_text="VMP Name",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="VMP Abbreviated name",
    )
    basiscd = models.ForeignKey(
        to="BasisOfName",
        on_delete=models.CASCADE,
        help_text="Basis of preferred name",
    )
    nmdt = models.DateField(
        null=True,
        help_text="Date of Name applicability",
    )
    nmprev = models.CharField(
        max_length=255,
        null=True,
        help_text="Previous Name",
    )
    basis_prevcd = models.ForeignKey(
        to="BasisOfName",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Basis of previous name",
    )
    nmchangecd = models.ForeignKey(
        to="NamechangeReason",
        on_delete=models.CASCADE,
        null=True,
        help_text="Reason for name change",
    )
    combprodcd = models.ForeignKey(
        to="CombinationProdInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination product Indicator",
    )
    pres_statcd = models.ForeignKey(
        to="VirtualProductPresStatus",
        on_delete=models.CASCADE,
        help_text="VMP Prescribing Status",
    )
    sug_f = models.BooleanField(
        help_text="Sugar Free Indicator",
    )
    glu_f = models.BooleanField(
        help_text="Gluten Free Indicator",
    )
    pres_f = models.BooleanField(
        help_text="Preservative Free Indicator",
    )
    cfc_f = models.BooleanField(
        help_text="CFC Free Indicator",
    )
    non_availcd = models.ForeignKey(
        to="VirtualProductNonAvail",
        on_delete=models.CASCADE,
        null=True,
        help_text="Non-availability indicator",
    )
    non_availdt = models.DateField(
        null=True,
        help_text="Non availability status date",
    )
    df_indcd = models.ForeignKey(
        to="DfIndicator",
        on_delete=models.CASCADE,
        null=True,
        help_text="Dose form indicator",
    )
    udfs = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        help_text="Unit dose form size",
    )
    udfs_uomcd = models.ForeignKey(
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Unit dose form units",
    )
    unit_dose_uomcd = models.ForeignKey(
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Unit dose unit of measure",
    )


class VPI(models.Model):
    vpid = models.IntegerField(
        primary_key=True,
        help_text="VMP identifier",
    )
    isid = models.ForeignKey(
        to="Ing",
        on_delete=models.CASCADE,
        help_text="Ingredient substance identifier",
    )
    basis_strntcd = models.ForeignKey(
        to="BasisOfStrnth",
        on_delete=models.CASCADE,
        null=True,
        help_text="Basis of pharmaceutical strength",
    )
    bs_subid = models.IntegerField(
        null=True,
        help_text="Basis of strength substance identifier",
    )
    strnt_nmrtr_val = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        help_text="Strength value numerator",
    )
    strnt_nmrtr_uomcd = models.ForeignKey(
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Strength value numerator unit",
    )
    strnt_dnmtr_val = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        help_text="Strength value denominator",
    )
    strnt_dnmtr_uomcd = models.ForeignKey(
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Strength value denominator unit",
    )


class Ont(models.Model):
    vpid = models.IntegerField(
        primary_key=True,
        help_text="VMP ID",
    )
    formcd = models.ForeignKey(
        to="OntFormRoute",
        on_delete=models.CASCADE,
        help_text="VMP Form & Route",
    )


class Dform(models.Model):
    vpid = models.IntegerField(
        primary_key=True,
        help_text="VMP identifier",
    )
    formcd = models.ForeignKey(
        to="Form",
        on_delete=models.CASCADE,
        help_text="Formulation code",
    )


class Droute(models.Model):
    vpid = models.IntegerField(
        primary_key=True,
        help_text="VMP identifier",
    )
    routecd = models.ForeignKey(
        to="Route",
        on_delete=models.CASCADE,
        help_text="Route code",
    )


class ControlInfo(models.Model):
    vpid = models.IntegerField(
        primary_key=True,
        help_text="VMP identifier",
    )
    catcd = models.ForeignKey(
        to="ControlDrugCategory",
        on_delete=models.CASCADE,
        help_text="Control Drug category",
    )
    catdt = models.DateField(
        null=True,
        help_text="Date of applicability",
    )
    cat_prevcd = models.ForeignKey(
        to="ControlDrugCategory",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Previous Control Drug Information",
    )


class AMP(models.Model):
    apid = models.IntegerField(
        primary_key=True,
        help_text="AMP identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    vpid = models.ForeignKey(
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP identifier",
    )
    nm = models.CharField(
        max_length=255,
        help_text="AMP Name",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="AMP Abbreviated name",
    )
    desc = models.CharField(
        max_length=700,
        help_text="Description",
    )
    nmdt = models.DateField(
        null=True,
        help_text="Date of name applicability",
    )
    nm_prev = models.CharField(
        max_length=255,
        null=True,
        help_text="Previous Name",
    )
    suppcd = models.ForeignKey(
        to="Supplier",
        on_delete=models.CASCADE,
        help_text="Supplier",
    )
    lic_authcd = models.ForeignKey(
        to="LicensingAuthority",
        on_delete=models.CASCADE,
        help_text="Current Licensing Authority",
    )
    lic_auth_prevcd = models.ForeignKey(
        to="LicensingAuthority",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Previous Licensing Authority Code",
    )
    lic_authchangecd = models.ForeignKey(
        to="LicensingAuthorityChangeReason",
        on_delete=models.CASCADE,
        null=True,
        help_text="Reason for change of licensing authority code",
    )
    lic_authchangedt = models.DateField(
        null=True,
        help_text="Date of change of licensing authority",
    )
    combprodcd = models.ForeignKey(
        to="CombinationProdInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination product indicator Code",
    )
    flavourcd = models.ForeignKey(
        to="Flavour",
        on_delete=models.CASCADE,
        null=True,
        help_text="Flavour Code",
    )
    ema = models.BooleanField(
        help_text="EMA Additional Monitoring indicator",
    )
    parallel_import = models.BooleanField(
        help_text="Parallel Import indicator",
    )
    avail_restrictcd = models.ForeignKey(
        to="AvailabilityRestriction",
        on_delete=models.CASCADE,
        help_text="Restrictions on availability Code",
    )


class ApIng(models.Model):
    apid = models.IntegerField(
        primary_key=True,
        help_text="AMP",
    )
    isid = models.ForeignKey(
        to="Ing",
        on_delete=models.CASCADE,
        help_text="Ingredient substance identifier",
    )
    strnth = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        help_text="Pharmaceutical strength numerical value",
    )
    uomcd = models.ForeignKey(
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Pharmaceutical Strength Unit of Measure code",
    )


class LicRoute(models.Model):
    apid = models.IntegerField(
        primary_key=True,
        help_text="AMP identifier",
    )
    routecd = models.ForeignKey(
        to="Route",
        on_delete=models.CASCADE,
        help_text="Licenced route",
    )


class ApInfo(models.Model):
    apid = models.IntegerField(
        primary_key=True,
        help_text="AMP identifier",
    )
    sz_weight = models.CharField(
        max_length=100,
        null=True,
        help_text="Size / Weight",
    )
    colourcd = models.ForeignKey(
        to="Colour",
        on_delete=models.CASCADE,
        null=True,
        help_text="Colour code",
    )
    prod_order_no = models.CharField(
        max_length=20,
        null=True,
        help_text="Product order number",
    )


class VMPP(models.Model):
    vppid = models.IntegerField(
        primary_key=True,
        help_text="VMPP Identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    nm = models.CharField(
        max_length=420,
        help_text="VMPP description",
    )
    vpid = models.ForeignKey(
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP identifier",
    )
    qtyval = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        help_text="Quantity Value",
    )
    qty_uomcd = models.ForeignKey(
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Quantity Unit of Measure code",
    )
    combpackcd = models.ForeignKey(
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination pack indicator",
    )


class Dtinfo(models.Model):
    vppid = models.IntegerField(
        primary_key=True,
        help_text="VMPP identifier",
    )
    pay_catcd = models.ForeignKey(
        to="DtPaymentCategory",
        on_delete=models.CASCADE,
        help_text="Drug Tariff payment category code",
    )
    price = models.IntegerField(
        null=True,
        help_text="Drug Tariff Price",
    )
    dt = models.DateField(
        null=True,
        help_text="Date from which DT applicable",
    )
    prevprice = models.IntegerField(
        null=True,
        help_text="Previous price",
    )


class AMPP(models.Model):
    appid = models.IntegerField(
        primary_key=True,
        help_text="AMPP identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    nm = models.CharField(
        max_length=774,
        help_text="AMPP description",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="AMPP Abbreviated Name",
    )
    vppid = models.ForeignKey(
        to="VMPP",
        on_delete=models.CASCADE,
        help_text="VMPP identifier",
    )
    apid = models.ForeignKey(
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP identifier",
    )
    combpackcd = models.ForeignKey(
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination pack Indicator code",
    )
    legal_catcd = models.ForeignKey(
        to="LegalCategory",
        on_delete=models.CASCADE,
        help_text="Legal category code",
    )
    subp = models.CharField(
        max_length=30,
        null=True,
        help_text="Sub Pack Info",
    )
    disccd = models.ForeignKey(
        to="DiscontinuedInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Discontinued Flag code",
    )
    discdt = models.DateField(
        null=True,
        help_text="Discontinued Flag Change date",
    )


class PackInfo(models.Model):
    appid = models.IntegerField(
        primary_key=True,
        help_text="AMPP identifier as in AMPP tag above",
    )
    reimb_statcd = models.ForeignKey(
        to="ReimbursementStatus",
        on_delete=models.CASCADE,
        help_text="Appliance Reimbursement status code",
    )
    reimb_statdt = models.DateField(
        null=True,
        help_text="Date Appliance reimbursement status became effective",
    )
    reimb_statprevcd = models.ForeignKey(
        to="ReimbursementStatus",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Appliance Reimbursement previous status code",
    )
    pack_order_no = models.CharField(
        max_length=20,
        null=True,
        help_text="Pack order number",
    )


class PrescribInfo(models.Model):
    appid = models.IntegerField(
        primary_key=True,
        help_text="AMPP identifier",
    )
    sched_2 = models.BooleanField(
        help_text="Schedule 2 indicator",
    )
    acbs = models.BooleanField(
        help_text="ACBS indicator",
    )
    padm = models.BooleanField(
        help_text="Personally Administered indicator",
    )
    fp10_mda = models.BooleanField(
        help_text="FP10 MDA Prescription indicator",
    )
    sched_1 = models.BooleanField(
        help_text="Schedule 1 indicator",
    )
    hosp = models.BooleanField(
        help_text="Hospital indicator",
    )
    nurse_f = models.BooleanField(
        help_text="Nurse Formulary indicator",
    )
    enurse_f = models.BooleanField(
        help_text="Nurse Extended Formulary indicator",
    )
    dent_f = models.BooleanField(
        help_text="Dental Formulary indicator",
    )


class PriceInfo(models.Model):
    appid = models.IntegerField(
        primary_key=True,
        help_text="AMPP identifier",
    )
    price = models.IntegerField(
        null=True,
        help_text="Price",
    )
    pricedt = models.DateField(
        null=True,
        help_text="Date of price validity",
    )
    price_prev = models.IntegerField(
        null=True,
        help_text="Price prior to change date",
    )
    price_basiscd = models.ForeignKey(
        to="PriceBasis",
        on_delete=models.CASCADE,
        help_text="Price basis flag",
    )


class ReimbInfo(models.Model):
    appid = models.IntegerField(
        primary_key=True,
        help_text="AMPP identifier",
    )
    px_chrgs = models.IntegerField(
        null=True,
        help_text="Prescription Charges",
    )
    disp_fees = models.IntegerField(
        null=True,
        help_text="Dispensing Fees",
    )
    bb = models.BooleanField(
        help_text="Broken Bulk indicator",
    )
    cal_pack = models.BooleanField(
        help_text="Calendar pack indicator",
    )
    spec_contcd = models.ForeignKey(
        to="SpecCont",
        on_delete=models.CASCADE,
        null=True,
        help_text="Special Container Indicator code",
    )
    dnd = models.ForeignKey(
        to="Dnd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Discount Not Deducted Indicator",
    )
    fp34d = models.BooleanField(
        help_text="FP34D prescription item indicator",
    )


class Ing(models.Model):
    isid = models.IntegerField(
        primary_key=True,
        help_text="Ingredient Substance Identifier",
    )
    isiddt = models.DateField(
        null=True,
        help_text="Date ingredient substance identifier became valid",
    )
    isidprev = models.IntegerField(
        null=True,
        help_text="Previous ingredient substance identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    nm = models.CharField(
        max_length=255,
        help_text="Ingredient Substance Name",
    )


class CombinationPackInd(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class CombinationProdInd(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class BasisOfName(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=150,
        help_text="Description",
    )


class NamechangeReason(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=150,
        help_text="Description",
    )


class VirtualProductPresStatus(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class ControlDrugCategory(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class LicensingAuthority(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class UnitOfMeasure(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.IntegerField(
        null=True,
        help_text="Previous code",
    )
    desc = models.CharField(
        max_length=150,
        help_text="Description",
    )


class Form(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.IntegerField(
        null=True,
        help_text="Previous code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class OntFormRoute(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Route(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.IntegerField(
        null=True,
        help_text="Previous code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class DtPaymentCategory(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Supplier(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.IntegerField(
        null=True,
        help_text="Previous code",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    desc = models.CharField(
        max_length=80,
        help_text="Description",
    )


class Flavour(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Colour(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class BasisOfStrnth(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=150,
        help_text="Description",
    )


class ReimbursementStatus(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class SpecCont(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Dnd(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class VirtualProductNonAvail(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class DiscontinuedInd(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class DfIndicator(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=20,
        help_text="Description",
    )


class PriceBasis(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class LegalCategory(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class AvailabilityRestriction(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class LicensingAuthorityChangeReason(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    desc = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Gtin(models.Model):
    appid = models.IntegerField(
        primary_key=True,
        help_text="AMPP identifier",
    )
    gtin = models.IntegerField(
        help_text="GTIN",
    )
    startdt = models.DateField(
        help_text="GTIN date",
    )
    enddt = models.DateField(
        null=True,
        help_text="The date the GTIN became invalid",
    )
