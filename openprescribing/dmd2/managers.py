from django.db import models


class DMDObjectQuerySet(models.QuerySet):
    def search(self, q):
        kwargs = {"{}__icontains".format(self.model.name_field): q}
        return self.filter(**kwargs)

    def valid(self):
        return self.exclude(invalid=True)

    def available(self):
        raise NotImplementedError

    def with_bnf_code(self):
        return self.filter(bnf_code__isnull=False)

    def valid_and_available(self):
        return self.valid().available()


class VTMQuerySet(DMDObjectQuerySet):
    def available(self):
        # There are no fields on VTM relating to availability
        return self

    def with_bnf_code(self):
        # We can't match BNF codes against VTMs
        return self


class VMPQuerySet(DMDObjectQuerySet):
    def available(self):
        # non_availcd = 1 corresponds to "Actual Products not Available"
        return self.exclude(non_avail_id=1)


class VMPPQuerySet(DMDObjectQuerySet):
    def available(self):
        # There are no fields on VMPP relating to availability
        return self


class AMPQuerySet(DMDObjectQuerySet):
    def available(self):
        # avail_restrictcd = 9 corresponds to "Actual Products not Available"
        return self.exclude(avail_restrict_id=9)


class AMPPQuerySet(DMDObjectQuerySet):
    def available(self):
        # disccd = 1 corresponds to "Discontinued Flag"
        return self.exclude(disc_id=1)


VTMManager = VTMQuerySet.as_manager
VMPManager = VMPQuerySet.as_manager
VMPPManager = VMPPQuerySet.as_manager
AMPManager = AMPQuerySet.as_manager
AMPPManager = AMPPQuerySet.as_manager
