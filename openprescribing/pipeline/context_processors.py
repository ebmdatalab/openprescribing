from pipeline.runner import in_progress


def import_in_progress(request):
    return {'import_in_progess': in_progress()}
