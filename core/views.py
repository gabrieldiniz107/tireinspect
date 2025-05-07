# core/views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.views.decorators.http import require_POST

from .models import Company, Truck, Inspection, Tire
from .forms  import (
    CompanyForm, TruckForm,
    InspectionForm, TireFormSet,
    UserRegisterForm
)


# ---------------------------------------------------------
# 0. Auth helpers
# ---------------------------------------------------------
def index(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    return redirect("core:login")


@login_required
def home(request):
    return render(request, "core/home.html")


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("core:home")
    else:
        form = UserRegisterForm()
    return render(request, "core/register.html", {"form": form})


# ---------------------------------------------------------
# 1. Empresas
# ---------------------------------------------------------
@login_required
def company_list(request):
    companies = Company.objects.filter(created_by=request.user)
    return render(request, "core/company_list.html", {"companies": companies})


@login_required
def company_create(request):
    form = CompanyForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return redirect("core:company_list")
    return render(request, "core/form.html",
                  {"form": form, "title": "Nova empresa"})

@login_required
@require_POST
def company_delete(request, company_id):
    company = get_object_or_404(Company, pk=company_id, created_by=request.user)
    company.delete()
    return redirect("core:company_list")

# ---------------------------------------------------------
# 2. Caminhões
# ---------------------------------------------------------
@login_required
def truck_list(request, company_id):
    company = get_object_or_404(
        Company, pk=company_id, created_by=request.user
    )
    return render(request, "core/truck_list.html", {"company": company})


@login_required
@login_required
def truck_create(request, company_id):
    company = get_object_or_404(Company, pk=company_id, created_by=request.user)
    form = TruckForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        plate = form.cleaned_data["plate"]
        # Valida duplicata
        if Truck.objects.filter(company=company, plate__iexact=plate).exists():
            form.add_error("plate", "Já existe um caminhão com essa placa para esta empresa.")
        else:
            truck = form.save(commit=False)
            truck.company = company
            truck.save()
            return redirect("core:truck_list", company_id=company.id)
    return render(request, "core/form.html", {
        "form": form,
        "title": f"Adicionar caminhão – {company.name}",
    })

# ---------------------------------------------------------
# 3. Inspeções
# ---------------------------------------------------------
@login_required
def inspection_list(request, truck_id):
    truck = get_object_or_404(
        Truck, pk=truck_id, company__created_by=request.user
    )
    return render(request, "core/inspection_list.html", {"truck": truck})


@login_required
def inspection_create(request, truck_id):
    truck = get_object_or_404(
        Truck, pk=truck_id, company__created_by=request.user
    )
    inspection = Inspection(truck=truck)
    tire_extra = truck.truck_type.tire_count

    TireFormSetDynamic = inlineformset_factory(
        Inspection, Tire,
        form=TireFormSet.form,
        extra=tire_extra, can_delete=False
    )

    if request.method == "POST":
        form = InspectionForm(request.POST, instance=inspection)
        formset = TireFormSetDynamic(request.POST, instance=inspection)

        # atribui posições 1..n antes da validação final
        if formset.is_valid():
            for idx, f in enumerate(formset.forms, start=1):
                f.instance.position = idx

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("core:inspection_detail", inspection_id=inspection.id)
    else:
        initial = [{"position": i} for i in range(1, tire_extra + 1)]
        form = InspectionForm(instance=inspection)
        formset = TireFormSetDynamic(instance=inspection, initial=initial)

    return render(request, "core/inspection_form.html",
                  {"form": form, "formset": formset, "truck": truck})


@login_required
def inspection_edit(request, inspection_id):
    inspection = get_object_or_404(
        Inspection, pk=inspection_id,
        truck__company__created_by=request.user
    )
    TireFormSetDynamic = inlineformset_factory(
        Inspection, Tire,
        form=TireFormSet.form,
        extra=0, can_delete=False
    )

    if request.method == "POST":
        form = InspectionForm(request.POST, instance=inspection)
        formset = TireFormSetDynamic(request.POST, instance=inspection)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("core:inspection_detail", inspection_id=inspection.id)
    else:
        form = InspectionForm(instance=inspection)
        formset = TireFormSetDynamic(instance=inspection)

    return render(request, "core/inspection_form.html",
                  {"form": form, "formset": formset, "truck": inspection.truck})


@login_required
def inspection_detail(request, inspection_id):
    inspection = get_object_or_404(
        Inspection, pk=inspection_id,
        truck__company__created_by=request.user
    )
    return render(request, "core/inspection_detail.html",
                  {"inspection": inspection})

from django.views.decorators.http import require_POST

@login_required
@require_POST
def inspection_delete(request, inspection_id):
    insp = get_object_or_404(
        Inspection,
        pk=inspection_id,
        truck__company__created_by=request.user
    )
    truck_id = insp.truck.id
    insp.delete()
    # volta para a lista de inspeções desse caminhão
    return redirect("core:inspection_list", truck_id=truck_id)

