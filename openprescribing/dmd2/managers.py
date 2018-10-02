from django.db import models


class DMDObjectQuerySet(models.QuerySet):
    def search(self, q):
        kwargs = {"{}__icontains".format(self.search_field): q}
        return self.filter(**kwargs)

    def valid(self):
        return self.exclude(invalid=True)

    def valid_and_available(self):
        return self.valid().available()

    def available(self, q):
        raise NotImplementedError


class VTMQuerySet(DMDObjectQuerySet):
    search_field = "nm"

    def available(self):
        # There are no fields on VTM relating to availability
        return self


class VMPQuerySet(DMDObjectQuerySet):
    search_field = "nm"

    def available(self):
        # non_availcd = 1 corresponds to "Actual Products not Available"
        return self.exclude(non_avail_id=1)


class VMPPQuerySet(DMDObjectQuerySet):
    search_field = "nm"

    def available(self):
        # There are no fields on VMPP relating to availability
        return self


class AMPQuerySet(DMDObjectQuerySet):
    search_field = "descr"

    def available(self):
        # avail_restrictcd = 9 corresponds to "Actual Products not Available"
        return self.exclude(avail_restrict_id=9)


class AMPPQuerySet(DMDObjectQuerySet):
    search_field = "nm"

    def available(self):
        # disccd = 1 corresponds to "Discontinued Flag"
        return self.exclude(disc_id=1)


VTMManager = VTMQuerySet.as_manager
VMPManager = VMPQuerySet.as_manager
VMPPManager = VMPPQuerySet.as_manager
AMPManager = AMPQuerySet.as_manager
AMPPManager = AMPPQuerySet.as_manager
