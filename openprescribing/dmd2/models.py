from django.db import models


class VTM(models.Model):
    id = models.BigIntegerField(
        primary_key=True,
        db_column="vtmid",
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
    vtmidprev = models.BigIntegerField(
        null=True,
        help_text="Previous VTM identifier",
    )
    vtmiddt = models.DateField(
        null=True,
        help_text="VTM Identifier date",
    )


class VMP(models.Model):
    id = models.BigIntegerField(
        primary_key=True,
        db_column="vpid",
        help_text="VMP identifier",
    )
    vpiddt = models.DateField(
        null=True,
        help_text="Date VMP identifier became Valid",
    )
    vpidprev = models.BigIntegerField(
        null=True,
        help_text="Previous product identifier",
    )
    vtm = models.ForeignKey(
        db_column="vtmid",
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
    basis = models.ForeignKey(
        db_column="basiscd",
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
    basis_prev = models.ForeignKey(
        db_column="basis_prevcd",
        to="BasisOfName",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Basis of previous name",
    )
    nmchange = models.ForeignKey(
        db_column="nmchangecd",
        to="NamechangeReason",
        on_delete=models.CASCADE,
        null=True,
        help_text="Reason for name change",
    )
    combprod = models.ForeignKey(
        db_column="combprodcd",
        to="CombinationProdInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination product Indicator",
    )
    pres_stat = models.ForeignKey(
        db_column="pres_statcd",
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
    non_avail = models.ForeignKey(
        db_column="non_availcd",
        to="VirtualProductNonAvail",
        on_delete=models.CASCADE,
        null=True,
        help_text="Non-availability indicator",
    )
    non_availdt = models.DateField(
        null=True,
        help_text="Non availability status date",
    )
    df_ind = models.ForeignKey(
        db_column="df_indcd",
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
    udfs_uom = models.ForeignKey(
        db_column="udfs_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Unit dose form units",
    )
    unit_dose_uom = models.ForeignKey(
        db_column="unit_dose_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Unit dose unit of measure",
    )


class VPI(models.Model):
    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP identifier",
    )
    ing = models.ForeignKey(
        db_column="isid",
        to="Ing",
        on_delete=models.CASCADE,
        help_text="Ingredient substance identifier",
    )
    basis_strnt = models.ForeignKey(
        db_column="basis_strntcd",
        to="BasisOfStrnth",
        on_delete=models.CASCADE,
        null=True,
        help_text="Basis of pharmaceutical strength",
    )
    bs_subid = models.BigIntegerField(
        null=True,
        help_text="Basis of strength substance identifier",
    )
    strnt_nmrtr_val = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        help_text="Strength value numerator",
    )
    strnt_nmrtr_uom = models.ForeignKey(
        db_column="strnt_nmrtr_uomcd",
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
    strnt_dnmtr_uom = models.ForeignKey(
        db_column="strnt_dnmtr_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Strength value denominator unit",
    )


class Ont(models.Model):
    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP ID",
    )
    form = models.ForeignKey(
        db_column="formcd",
        to="OntFormRoute",
        on_delete=models.CASCADE,
        help_text="VMP Form & Route",
    )


class Dform(models.Model):
    vmp = models.OneToOneField(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP identifier",
    )
    form = models.ForeignKey(
        db_column="formcd",
        to="Form",
        on_delete=models.CASCADE,
        help_text="Formulation code",
    )


class Droute(models.Model):
    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP identifier",
    )
    route = models.ForeignKey(
        db_column="routecd",
        to="Route",
        on_delete=models.CASCADE,
        help_text="Route code",
    )


class ControlInfo(models.Model):
    vmp = models.OneToOneField(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP identifier",
    )
    cat = models.ForeignKey(
        db_column="catcd",
        to="ControlDrugCategory",
        on_delete=models.CASCADE,
        help_text="Control Drug category",
    )
    catdt = models.DateField(
        null=True,
        help_text="Date of applicability",
    )
    cat_prev = models.ForeignKey(
        db_column="cat_prevcd",
        to="ControlDrugCategory",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Previous Control Drug Information",
    )


class AMP(models.Model):
    id = models.BigIntegerField(
        primary_key=True,
        db_column="apid",
        help_text="AMP identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    vmp = models.ForeignKey(
        db_column="vpid",
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
    descr = models.CharField(
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
    supp = models.ForeignKey(
        db_column="suppcd",
        to="Supplier",
        on_delete=models.CASCADE,
        help_text="Supplier",
    )
    lic_auth = models.ForeignKey(
        db_column="lic_authcd",
        to="LicensingAuthority",
        on_delete=models.CASCADE,
        help_text="Current Licensing Authority",
    )
    lic_auth_prev = models.ForeignKey(
        db_column="lic_auth_prevcd",
        to="LicensingAuthority",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Previous Licensing Authority Code",
    )
    lic_authchange = models.ForeignKey(
        db_column="lic_authchangecd",
        to="LicensingAuthorityChangeReason",
        on_delete=models.CASCADE,
        null=True,
        help_text="Reason for change of licensing authority code",
    )
    lic_authchangedt = models.DateField(
        null=True,
        help_text="Date of change of licensing authority",
    )
    combprod = models.ForeignKey(
        db_column="combprodcd",
        to="CombinationProdInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination product indicator Code",
    )
    flavour = models.ForeignKey(
        db_column="flavourcd",
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
    avail_restrict = models.ForeignKey(
        db_column="avail_restrictcd",
        to="AvailabilityRestriction",
        on_delete=models.CASCADE,
        help_text="Restrictions on availability Code",
    )


class ApIng(models.Model):
    amp = models.ForeignKey(
        db_column="apid",
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP",
    )
    ing = models.ForeignKey(
        db_column="isid",
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
    uom = models.ForeignKey(
        db_column="uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Pharmaceutical Strength Unit of Measure code",
    )


class LicRoute(models.Model):
    amp = models.ForeignKey(
        db_column="apid",
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP identifier",
    )
    route = models.ForeignKey(
        db_column="routecd",
        to="Route",
        on_delete=models.CASCADE,
        help_text="Licenced route",
    )


class ApInfo(models.Model):
    amp = models.OneToOneField(
        db_column="apid",
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP identifier",
    )
    sz_weight = models.CharField(
        max_length=100,
        null=True,
        help_text="Size / Weight",
    )
    colour = models.ForeignKey(
        db_column="colourcd",
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
    id = models.BigIntegerField(
        primary_key=True,
        db_column="vppid",
        help_text="VMPP Identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    nm = models.CharField(
        max_length=420,
        help_text="VMPP description",
    )
    vmp = models.ForeignKey(
        db_column="vpid",
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
    qty_uom = models.ForeignKey(
        db_column="qty_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Quantity Unit of Measure code",
    )
    combpack = models.ForeignKey(
        db_column="combpackcd",
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination pack indicator",
    )


class Dtinfo(models.Model):
    vmpp = models.OneToOneField(
        db_column="vppid",
        to="VMPP",
        on_delete=models.CASCADE,
        help_text="VMPP identifier",
    )
    pay_cat = models.ForeignKey(
        db_column="pay_catcd",
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
    id = models.BigIntegerField(
        primary_key=True,
        db_column="appid",
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
    vmpp = models.ForeignKey(
        db_column="vppid",
        to="VMPP",
        on_delete=models.CASCADE,
        help_text="VMPP identifier",
    )
    amp = models.ForeignKey(
        db_column="apid",
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP identifier",
    )
    combpack = models.ForeignKey(
        db_column="combpackcd",
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination pack Indicator code",
    )
    legal_cat = models.ForeignKey(
        db_column="legal_catcd",
        to="LegalCategory",
        on_delete=models.CASCADE,
        help_text="Legal category code",
    )
    subp = models.CharField(
        max_length=30,
        null=True,
        help_text="Sub Pack Info",
    )
    disc = models.ForeignKey(
        db_column="disccd",
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
    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
        help_text="AMPP identifier as in AMPP tag above",
    )
    reimb_stat = models.ForeignKey(
        db_column="reimb_statcd",
        to="ReimbursementStatus",
        on_delete=models.CASCADE,
        help_text="Appliance Reimbursement status code",
    )
    reimb_statdt = models.DateField(
        null=True,
        help_text="Date Appliance reimbursement status became effective",
    )
    reimb_statprev = models.ForeignKey(
        db_column="reimb_statprevcd",
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
    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
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
    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
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
    price_basis = models.ForeignKey(
        db_column="price_basiscd",
        to="PriceBasis",
        on_delete=models.CASCADE,
        help_text="Price basis flag",
    )


class ReimbInfo(models.Model):
    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
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
    spec_cont = models.ForeignKey(
        db_column="spec_contcd",
        to="SpecCont",
        on_delete=models.CASCADE,
        null=True,
        help_text="Special Container Indicator code",
    )
    dnd = models.ForeignKey(
        db_column="dndcd",
        to="Dnd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Discount Not Deducted Indicator",
    )
    fp34d = models.BooleanField(
        help_text="FP34D prescription item indicator",
    )


class Ing(models.Model):
    id = models.BigIntegerField(
        primary_key=True,
        db_column="isid",
        help_text="Ingredient Substance Identifier",
    )
    isiddt = models.DateField(
        null=True,
        help_text="Date ingredient substance identifier became valid",
    )
    isidprev = models.BigIntegerField(
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
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class CombinationProdInd(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class BasisOfName(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=150,
        help_text="Description",
    )


class NamechangeReason(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=150,
        help_text="Description",
    )


class VirtualProductPresStatus(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class ControlDrugCategory(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class LicensingAuthority(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class UnitOfMeasure(models.Model):
    cd = models.BigIntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.BigIntegerField(
        null=True,
        help_text="Previous code",
    )
    descr = models.CharField(
        max_length=150,
        help_text="Description",
    )


class Form(models.Model):
    cd = models.BigIntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.BigIntegerField(
        null=True,
        help_text="Previous code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class OntFormRoute(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Route(models.Model):
    cd = models.BigIntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.BigIntegerField(
        null=True,
        help_text="Previous code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class DtPaymentCategory(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Supplier(models.Model):
    cd = models.BigIntegerField(
        primary_key=True,
        help_text="Code",
    )
    cddt = models.DateField(
        null=True,
        help_text="Date code is applicable from",
    )
    cdprev = models.BigIntegerField(
        null=True,
        help_text="Previous code",
    )
    invalid = models.BooleanField(
        help_text="Invalidity flag",
    )
    descr = models.CharField(
        max_length=80,
        help_text="Description",
    )


class Flavour(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Colour(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class BasisOfStrnth(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=150,
        help_text="Description",
    )


class ReimbursementStatus(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class SpecCont(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class Dnd(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class VirtualProductNonAvail(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class DiscontinuedInd(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class DfIndicator(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=20,
        help_text="Description",
    )


class PriceBasis(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class LegalCategory(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class AvailabilityRestriction(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class LicensingAuthorityChangeReason(models.Model):
    cd = models.IntegerField(
        primary_key=True,
        help_text="Code",
    )
    descr = models.CharField(
        max_length=60,
        help_text="Description",
    )


class GTIN(models.Model):
    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
        help_text="AMPP identifier",
    )
    gtin = models.BigIntegerField(
        help_text="GTIN",
    )
    startdt = models.DateField(
        help_text="GTIN date",
    )
    enddt = models.DateField(
        null=True,
        help_text="The date the GTIN became invalid",
    )
