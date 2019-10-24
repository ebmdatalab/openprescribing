from .models import VTM, VMP, VMPP, AMP, AMPP


obj_types = ["vtm", "vmp", "vmpp", "amp", "ampp"]
obj_type_to_cls = {"vtm": VTM, "vmp": VMP, "vmpp": VMPP, "amp": AMP, "ampp": AMPP}
cls_to_obj_type = {cls: obj_type for obj_type, cls in obj_type_to_cls.items()}
clss = list(cls_to_obj_type)
