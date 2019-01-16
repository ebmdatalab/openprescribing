from django.db import models

from . import managers


class VTM(models.Model):
    class Meta:
        verbose_name = "Virtual Therapeutic Moiety"
        verbose_name_plural = "Virtual Therapeutic Moieties"
        ordering = ["nm"]

    objects = managers.VTMManager()

    obj_type = "vtm"
    name_field = "nm"

    def __str__(self):
        return str(self.id)

    id = models.BigIntegerField(
        primary_key=True,
        db_column="vtmid",
        help_text="Identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalid",
    )
    nm = models.CharField(
        max_length=255,
        help_text="Name",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="Abbreviated name",
    )
    vtmidprev = models.BigIntegerField(
        null=True,
        help_text="Previous identifier",
    )
    vtmiddt = models.DateField(
        null=True,
        help_text="VTM identifier date",
    )

    def title(self):
        return self.nm


class VMP(models.Model):
    class Meta:
        verbose_name = "Virtual Medicinal Product"
        ordering = ["nm"]

    objects = managers.VMPManager()

    obj_type = "vmp"
    name_field = "nm"

    def __str__(self):
        return str(self.id)

    id = models.BigIntegerField(
        primary_key=True,
        db_column="vpid",
        help_text="Identifier",
    )
    vpiddt = models.DateField(
        null=True,
        help_text="Date identifier became valid",
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
        help_text="VTM",
    )
    invalid = models.BooleanField(
        help_text="Invalid",
    )
    nm = models.CharField(
        max_length=255,
        help_text="Name",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="Abbreviated name",
    )
    basis = models.ForeignKey(
        db_column="basiscd",
        to="BasisOfName",
        on_delete=models.CASCADE,
        help_text="Basis of preferred name",
    )
    nmdt = models.DateField(
        null=True,
        help_text="Date of name applicability",
    )
    nmprev = models.CharField(
        max_length=255,
        null=True,
        help_text="Previous name",
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
        help_text="Combination product",
    )
    pres_stat = models.ForeignKey(
        db_column="pres_statcd",
        to="VirtualProductPresStatus",
        on_delete=models.CASCADE,
        help_text="Prescribing status",
    )
    sug_f = models.BooleanField(
        help_text="Sugar free",
    )
    glu_f = models.BooleanField(
        help_text="Gluten free",
    )
    pres_f = models.BooleanField(
        help_text="Preservative free",
    )
    cfc_f = models.BooleanField(
        help_text="CFC free",
    )
    non_avail = models.ForeignKey(
        db_column="non_availcd",
        to="VirtualProductNonAvail",
        on_delete=models.CASCADE,
        null=True,
        help_text="Non-availability",
    )
    non_availdt = models.DateField(
        null=True,
        help_text="Non-availability status date",
    )
    df_ind = models.ForeignKey(
        db_column="df_indcd",
        to="DfIndicator",
        on_delete=models.CASCADE,
        null=True,
        help_text="Dose form",
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
    bnf_code = models.CharField(max_length=15, null=True)

    def title(self):
        return self.nm


class VPI(models.Model):
    class Meta:
        verbose_name = "Virtual Product Ingredient"

    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP",
    )
    ing = models.ForeignKey(
        db_column="isid",
        to="Ing",
        on_delete=models.CASCADE,
        help_text="Ingredient",
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
    class Meta:
        verbose_name = "Ontology Drug Form & Route"

    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP",
    )
    form = models.ForeignKey(
        db_column="formcd",
        to="OntFormRoute",
        on_delete=models.CASCADE,
        help_text="Form & Route",
    )


class Dform(models.Model):
    class Meta:
        verbose_name = "Dose Form"

    vmp = models.OneToOneField(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP",
    )
    form = models.ForeignKey(
        db_column="formcd",
        to="Form",
        on_delete=models.CASCADE,
        help_text="Formulation",
    )


class Droute(models.Model):
    class Meta:
        verbose_name = "Drug Route"

    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP",
    )
    route = models.ForeignKey(
        db_column="routecd",
        to="Route",
        on_delete=models.CASCADE,
        help_text="Route",
    )


class ControlInfo(models.Model):
    class Meta:
        verbose_name = "Controlled Drug Prescribing Information"

    vmp = models.OneToOneField(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP",
    )
    cat = models.ForeignKey(
        db_column="catcd",
        to="ControlDrugCategory",
        on_delete=models.CASCADE,
        help_text="Controlled Drug category",
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
        help_text="Previous Controlled Drug information",
    )


class AMP(models.Model):
    class Meta:
        verbose_name = "Actual Medicinal Product"
        ordering = ["descr"]

    objects = managers.AMPManager()

    obj_type = "amp"
    name_field = "descr"

    def __str__(self):
        return str(self.id)

    id = models.BigIntegerField(
        primary_key=True,
        db_column="apid",
        help_text="Identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalid",
    )
    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP",
    )
    nm = models.CharField(
        max_length=255,
        help_text="Name",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="Abbreviated name",
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
        help_text="Previous name",
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
        help_text="Current licensing authority",
    )
    lic_auth_prev = models.ForeignKey(
        db_column="lic_auth_prevcd",
        to="LicensingAuthority",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Previous licensing authority",
    )
    lic_authchange = models.ForeignKey(
        db_column="lic_authchangecd",
        to="LicensingAuthorityChangeReason",
        on_delete=models.CASCADE,
        null=True,
        help_text="Reason for change of licensing authority",
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
        help_text="Combination product",
    )
    flavour = models.ForeignKey(
        db_column="flavourcd",
        to="Flavour",
        on_delete=models.CASCADE,
        null=True,
        help_text="Flavour",
    )
    ema = models.BooleanField(
        help_text="EMA additional monitoring",
    )
    parallel_import = models.BooleanField(
        help_text="Parallel import",
    )
    avail_restrict = models.ForeignKey(
        db_column="avail_restrictcd",
        to="AvailabilityRestriction",
        on_delete=models.CASCADE,
        help_text="Restrictions on availability",
    )
    bnf_code = models.CharField(max_length=15, null=True)

    def title(self):
        return self.descr


class ApIng(models.Model):
    class Meta:
        verbose_name = "TODO"

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
        help_text="Ingredient",
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
        help_text="Pharmaceutical Strength Unit of Measure",
    )


class LicRoute(models.Model):
    class Meta:
        verbose_name = "Licensed Route"

    amp = models.ForeignKey(
        db_column="apid",
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP",
    )
    route = models.ForeignKey(
        db_column="routecd",
        to="Route",
        on_delete=models.CASCADE,
        help_text="Licenced route",
    )


class ApInfo(models.Model):
    class Meta:
        verbose_name = "Appliance Product Information"

    amp = models.OneToOneField(
        db_column="apid",
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP",
    )
    sz_weight = models.CharField(
        max_length=100,
        null=True,
        help_text="Size / weight",
    )
    colour = models.ForeignKey(
        db_column="colourcd",
        to="Colour",
        on_delete=models.CASCADE,
        null=True,
        help_text="Colour",
    )
    prod_order_no = models.CharField(
        max_length=20,
        null=True,
        help_text="Product order number",
    )


class VMPP(models.Model):
    class Meta:
        verbose_name = "Virtual Medicinal Product Pack"
        ordering = ["nm"]

    objects = managers.VMPPManager()

    obj_type = "vmpp"
    name_field = "nm"

    def __str__(self):
        return str(self.id)

    id = models.BigIntegerField(
        primary_key=True,
        db_column="vppid",
        help_text="Identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalid",
    )
    nm = models.CharField(
        max_length=420,
        help_text="Description",
    )
    vmp = models.ForeignKey(
        db_column="vpid",
        to="VMP",
        on_delete=models.CASCADE,
        help_text="VMP",
    )
    qtyval = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        help_text="Quantity value",
    )
    qty_uom = models.ForeignKey(
        db_column="qty_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Quantity unit of measure",
    )
    combpack = models.ForeignKey(
        db_column="combpackcd",
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination pack",
    )
    bnf_code = models.CharField(max_length=15, null=True)

    def title(self):
        return self.nm


class Dtinfo(models.Model):
    class Meta:
        verbose_name = "Drug Tariff Category Information"

    vmpp = models.OneToOneField(
        db_column="vppid",
        to="VMPP",
        on_delete=models.CASCADE,
        help_text="VMPP",
    )
    pay_cat = models.ForeignKey(
        db_column="pay_catcd",
        to="DtPaymentCategory",
        on_delete=models.CASCADE,
        help_text="Drug Tariff payment category",
    )
    price = models.IntegerField(
        null=True,
        help_text="Drug Tariff price",
    )
    dt = models.DateField(
        null=True,
        help_text="Date from which applicable",
    )
    prevprice = models.IntegerField(
        null=True,
        help_text="Previous price",
    )


class AMPP(models.Model):
    class Meta:
        verbose_name = "Actual Medicinal Product Pack"
        ordering = ["nm"]

    objects = managers.AMPPManager()

    obj_type = "ampp"
    name_field = "nm"

    def __str__(self):
        return str(self.id)

    id = models.BigIntegerField(
        primary_key=True,
        db_column="appid",
        help_text="Identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalid",
    )
    nm = models.CharField(
        max_length=774,
        help_text="Description",
    )
    abbrevnm = models.CharField(
        max_length=60,
        null=True,
        help_text="Abbreviated name",
    )
    vmpp = models.ForeignKey(
        db_column="vppid",
        to="VMPP",
        on_delete=models.CASCADE,
        help_text="VMPP",
    )
    amp = models.ForeignKey(
        db_column="apid",
        to="AMP",
        on_delete=models.CASCADE,
        help_text="AMP",
    )
    combpack = models.ForeignKey(
        db_column="combpackcd",
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Combination pack",
    )
    legal_cat = models.ForeignKey(
        db_column="legal_catcd",
        to="LegalCategory",
        on_delete=models.CASCADE,
        help_text="Legal category",
    )
    subp = models.CharField(
        max_length=30,
        null=True,
        help_text="Sub pack info",
    )
    disc = models.ForeignKey(
        db_column="disccd",
        to="DiscontinuedInd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Discontinued",
    )
    discdt = models.DateField(
        null=True,
        help_text="Discontinued change date",
    )
    bnf_code = models.CharField(max_length=15, null=True)

    def title(self):
        return self.nm


class PackInfo(models.Model):
    class Meta:
        verbose_name = "TODO"

    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
        help_text="AMPP",
    )
    reimb_stat = models.ForeignKey(
        db_column="reimb_statcd",
        to="ReimbursementStatus",
        on_delete=models.CASCADE,
        help_text="Appliance reimbursement status",
    )
    reimb_statdt = models.DateField(
        null=True,
        help_text="Date appliance reimbursement status became effective",
    )
    reimb_statprev = models.ForeignKey(
        db_column="reimb_statprevcd",
        to="ReimbursementStatus",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="Appliance reimbursement previous status",
    )
    pack_order_no = models.CharField(
        max_length=20,
        null=True,
        help_text="Pack order number",
    )


class PrescribInfo(models.Model):
    class Meta:
        verbose_name = "Product Prescribing Information"

    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
        help_text="AMPP",
    )
    sched_2 = models.BooleanField(
        help_text="Schedule 2",
    )
    acbs = models.BooleanField(
        help_text="ACBS",
    )
    padm = models.BooleanField(
        help_text="Personally administered",
    )
    fp10_mda = models.BooleanField(
        help_text="FP10 MDA Prescription",
    )
    sched_1 = models.BooleanField(
        help_text="Schedule 1",
    )
    hosp = models.BooleanField(
        help_text="Hospital",
    )
    nurse_f = models.BooleanField(
        help_text="Nurse formulary",
    )
    enurse_f = models.BooleanField(
        help_text="Nurse extended formulary",
    )
    dent_f = models.BooleanField(
        help_text="Dental formulary",
    )


class PriceInfo(models.Model):
    class Meta:
        verbose_name = "Medicinal Product Price"

    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
        help_text="AMPP",
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
        help_text="Price basis",
    )


class ReimbInfo(models.Model):
    class Meta:
        verbose_name = "Reimbursement Information"

    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
        help_text="AMPP",
    )
    px_chrgs = models.IntegerField(
        null=True,
        help_text="Prescription charges",
    )
    disp_fees = models.IntegerField(
        null=True,
        help_text="Dispensing fees",
    )
    bb = models.BooleanField(
        help_text="Broken bulk",
    )
    cal_pack = models.BooleanField(
        help_text="Calendar pack",
    )
    spec_cont = models.ForeignKey(
        db_column="spec_contcd",
        to="SpecCont",
        on_delete=models.CASCADE,
        null=True,
        help_text="Special container",
    )
    dnd = models.ForeignKey(
        db_column="dndcd",
        to="Dnd",
        on_delete=models.CASCADE,
        null=True,
        help_text="Discount not deducted",
    )
    fp34d = models.BooleanField(
        help_text="FP34D prescription item",
    )


class Ing(models.Model):
    class Meta:
        verbose_name = "TODO"

    id = models.BigIntegerField(
        primary_key=True,
        db_column="isid",
        help_text="Identifier",
    )
    isiddt = models.DateField(
        null=True,
        help_text="Date identifier became valid",
    )
    isidprev = models.BigIntegerField(
        null=True,
        help_text="Previous identifier",
    )
    invalid = models.BooleanField(
        help_text="Invalid",
    )
    nm = models.CharField(
        max_length=255,
        help_text="Name",
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
        help_text="Invalid",
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
    class Meta:
        verbose_name = "Global Trade Item Number"

    ampp = models.OneToOneField(
        db_column="appid",
        to="AMPP",
        on_delete=models.CASCADE,
        help_text="AMPP",
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
