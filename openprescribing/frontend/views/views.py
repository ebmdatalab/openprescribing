from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from frontend.models import Chemical, Prescription, \
    Practice, PracticeStatistics, SHA, PCT, Section, \
    Measure


##################################################
# BNF SECTIONS
##################################################
def all_bnf(request):
    sections = Section.objects.all()
    context = {
        'sections': sections
    }
    return render(request, 'all_bnf.html', context)


def bnf_section(request, section_id):
    section = get_object_or_404(Section, bnf_id=section_id)
    id_len = len(section_id)
    bnf_chapter = None
    bnf_section = None
    try:
        if id_len > 2:
            bnf_chapter = Section.objects.get(bnf_id=section_id[:2])
        if id_len > 4:
            bnf_section = Section.objects.get(bnf_id=section_id[:4])
    except Section.DoesNotExist:
        pass
    chemicals = None
    subsections = Section.objects.filter(bnf_id__startswith=section_id) \
                         .extra(where=["CHAR_LENGTH(bnf_id)=%s" % (id_len+2)])
    if not subsections:
        chemicals = Chemical.objects.filter(bnf_code__startswith=section_id) \
                            .order_by('chem_name')
    context = {
        'section': section,
        'bnf_chapter': bnf_chapter,
        'bnf_section': bnf_section,
        'subsections': subsections,
        'chemicals': chemicals,
        'page_id': section_id
    }
    return render(request, 'bnf_section.html', context)


##################################################
# CHEMICALS
##################################################

def all_chemicals(request):
    chemicals = Chemical.objects.all().order_by('bnf_code')
    context = {
        'chemicals': chemicals
    }
    return render(request, 'all_chemicals.html', context)


def chemical(request, bnf_code):
    c = get_object_or_404(Chemical, bnf_code=bnf_code)

    # Get BNF chapter, section etc.
    bnf_chapter = Section.objects.get(bnf_id=bnf_code[:2])
    bnf_section = Section.objects.get(bnf_id=bnf_code[:4])
    try:
        bnf_para = Section.objects.get(bnf_id=bnf_code[:6])
    except Section.DoesNotExist:
        bnf_para = None

    context = {
        'page_id': bnf_code,
        'chemical': c,
        'bnf_chapter': bnf_chapter,
        'bnf_section': bnf_section,
        'bnf_para': bnf_para
    }
    return render(request, 'chemical.html', context)


##################################################
# GP PRACTICES
##################################################

def all_practices(request):
    practices = Practice.objects.filter(setting=4).order_by('name')
    context = {
        'practices': practices
    }
    return render(request, 'all_practices.html', context)


def practice(request, code):
    p = get_object_or_404(Practice, code=code)
    context = {
        'practice': p,
        'page_id': code,
        'page_type': 'practice'
    }
    return render(request, 'practice.html', context)


##################################################
# AREA TEAMS
##################################################

def all_area_teams(request):
    area_teams = SHA.objects.all().order_by('code')
    context = {
        'area_teams': area_teams
    }
    return render(request, 'all_area_teams.html', context)


def area_team(request, at_code):
    requested_at = get_object_or_404(SHA, code=at_code)
    prescriptions = Prescription.objects.filter(sha=requested_at)
    num_prescriptions = prescriptions.count()
    prescriptions_to_return = prescriptions[:100]
    context = {
        'area_team': requested_at,
        'num_prescriptions': num_prescriptions,
        'prescriptions': prescriptions_to_return
    }
    return render(request, 'area_team.html', context)


##################################################
# CCGs
##################################################

def all_ccgs(request):
    ccgs = PCT.objects.filter(org_type="CCG").order_by('name')
    context = {
        'ccgs': ccgs
    }
    return render(request, 'all_ccgs.html', context)


def ccg(request, ccg_code):
    requested_ccg = get_object_or_404(PCT, code=ccg_code)
    practices = Practice.objects.filter(ccg=requested_ccg).order_by('name')
    context = {
        'ccg': requested_ccg,
        'practices': practices,
        'page_id': ccg_code
    }
    return render(request, 'ccg.html', context)


def ccg_measure(request, ccg_code, measure):
    requested_ccg = get_object_or_404(PCT, code=ccg_code)
    measure = get_object_or_404(Measure, id=measure)
    practices = Practice.objects.filter(ccg=requested_ccg)\
        .filter(setting=4).order_by('name')
    context = {
        'ccg': requested_ccg,
        'practices': practices,
        'page_id': ccg_code,
        'measure': measure
    }
    return render(request, 'ccg_measure.html', context)

##################################################
# TEST HTTP CODES
##################################################
def test_500_view(request):
    return HttpResponse(status=500)
