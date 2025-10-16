# core/views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.forms import inlineformset_factory

from .models import Company, Truck, Inspection, Tire
from .forms import CompanyForm, TruckForm, TruckEditForm, InspectionForm, TireFormSet, UserRegisterForm


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
# 1. Empresa CRUD
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
    return render(request, "core/form.html", {"form": form, "title": "Nova empresa", "back_url": reverse("core:company_list")})


@login_required
@require_POST
def company_delete(request, company_id):
    company = get_object_or_404(Company, pk=company_id, created_by=request.user)
    company.delete()
    return redirect("core:company_list")


# ---------------------------------------------------------
# 2. Caminhão CRUD
# ---------------------------------------------------------
@login_required
def truck_list(request, company_id):
    company = get_object_or_404(Company, pk=company_id, created_by=request.user)
    return render(request, "core/truck_list.html", {"company": company})


@login_required
def truck_create(request, company_id):
    company = get_object_or_404(Company, pk=company_id, created_by=request.user)
    form = TruckForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        plate = form.cleaned_data["plate"]
        if Truck.objects.filter(company=company, plate__iexact=plate).exists():
            form.add_error("plate", "Já existe um caminhão com essa placa nesta empresa.")
        else:
            truck = form.save(commit=False)
            truck.company = company
            truck.save()
            return redirect("core:truck_list", company_id=company.id)
    return render(request, "core/form.html", {
        "form": form,
        "title": f"Adicionar caminhão – {company.name}",
        "back_url": reverse("core:truck_list", kwargs={"company_id": company.id}),
    })


@login_required
def truck_edit(request, truck_id):
    truck = get_object_or_404(Truck, pk=truck_id, company__created_by=request.user)
    company = truck.company
    form = TruckEditForm(request.POST or None, instance=truck)
    if request.method == "POST" and form.is_valid():
        # Garantir unicidade da placa por empresa
        plate = form.cleaned_data["plate"]
        exists = Truck.objects.filter(company=company, plate__iexact=plate).exclude(id=truck.id).exists()
        if exists:
            form.add_error("plate", "Já existe um caminhão com essa placa nesta empresa.")
        else:
            form.save()
            return redirect("core:truck_list", company_id=company.id)
    return render(request, "core/form.html", {
        "form": form,
        "title": f"Editar caminhão – {truck.plate}",
        "back_url": reverse("core:truck_list", kwargs={"company_id": company.id}),
    })


@login_required
@require_POST
def truck_delete(request, truck_id):
    truck = get_object_or_404(Truck, pk=truck_id, company__created_by=request.user)
    company_id = truck.company_id
    truck.delete()
    return redirect("core:truck_list", company_id=company_id)


# ---------------------------------------------------------
# Utils: rótulos de posição 1E,2E,3ED…1D,2D,3DD…
# ---------------------------------------------------------
def gerar_posicoes_personalizadas(axles: int, tires: int) -> list[str]:
    """
    Retorna exatamente `tires` labels na ordem:
      - Primeiro todos do lado esquerdo: 1E,2E, depois ED+EF nos eixos extras
      - Depois todos do lado direito: 1D,2D, depois DD+DF
    """
    # início: um pneu por eixo/lado
    left = [f"{i}E" for i in range(1, axles + 1)]
    right = [f"{i}D" for i in range(1, axles + 1)]
    # quantos pares extras (dual) substituir
    extra_pairs = (tires - axles * 2) // 2

    # do eixo mais alto para o 1, substitui
    for axle in range(axles, 0, -1):
        if extra_pairs <= 0:
            break
        idx = left.index(f"{axle}E")
        left[idx:idx+1] = [f"{axle}ED", f"{axle}EF"]
        idx = right.index(f"{axle}D")
        right[idx:idx+1] = [f"{axle}DD", f"{axle}DF"]
        extra_pairs -= 1

    return left + right


# ---------------------------------------------------------
# 3. Inspeções + Pneus
# ---------------------------------------------------------
@login_required
def inspection_list(request, truck_id):
    truck = get_object_or_404(Truck, pk=truck_id, company__created_by=request.user)
    return render(request, "core/inspection_list.html", {"truck": truck})


@login_required
def inspection_start(request, truck_id):
    """
    Tela intermediária que pergunta ao usuário se deseja
    reaproveitar a última inspeção (quando existir) ou
    iniciar uma nova em branco.
    """
    truck = get_object_or_404(Truck, pk=truck_id, company__created_by=request.user)
    last = truck.inspections.order_by("-date", "-id").first()
    return render(request, "core/inspection_start.html", {
        "truck": truck,
        "last": last,
    })


@login_required
def inspection_create(request, truck_id):
    truck = get_object_or_404(Truck, pk=truck_id, company__created_by=request.user)
    inspection = Inspection(truck=truck)
    tire_count = truck.truck_type.tire_count
    TireFS = inlineformset_factory(Inspection, Tire,
                                   form=TireFormSet.form,
                                   extra=tire_count, can_delete=False)

    if request.method == "POST":
        form = InspectionForm(request.POST, instance=inspection)
        formset = TireFS(request.POST, instance=inspection)
        if form.is_valid() and formset.is_valid():
            inspection = form.save()
            # salva numericamente 1..n (interno) e depois exibe labels
            for idx, tform in enumerate(formset.forms, start=1):
                tire = tform.save(commit=False)
                tire.inspection = inspection
                tire.position = idx
                tire.save()
            return redirect("core:inspection_detail", inspection_id=inspection.id)

    else:
        form = InspectionForm(instance=inspection)
        formset = TireFS(instance=inspection)
        # Se solicitado, carregar dados da última inspeção deste caminhão
        copy_flag = str(request.GET.get("copy_last", "")).lower() in ("1", "true", "yes")
        last = None
        if copy_flag:
            last = truck.inspections.order_by("-date", "-id").first()
        if last is not None:
            # Mapear pneus anteriores por posição
            prev_tires = list(last.tires.all().order_by("position"))
            for idx, tform in enumerate(formset.forms, start=1):
                if idx <= len(prev_tires):
                    pt = prev_tires[idx-1]
                    tform.initial.update({
                        "groove_1": pt.groove_1,
                        "groove_2": pt.groove_2,
                        "groove_3": pt.groove_3,
                        "brand": pt.brand,
                        "pattern": pt.pattern,
                        "fire_number": pt.fire_number,
                        "dot": pt.dot,
                        # ChoiceField espera string 'True'/'False' no widget
                        "rec": "True" if pt.rec else "False",
                    })
        # injeta labels (1E,2E,3ED…) no formset para exibição
        labels = gerar_posicoes_personalizadas(
            truck.truck_type.axle_count,
            truck.truck_type.tire_count
        )
        for idx, tform in enumerate(formset.forms):
            tform.position_label = labels[idx]

    return render(request, "core/inspection_form.html", {
        "form": form,
        "formset": formset,
        "truck": truck,
    })


@login_required
def inspection_edit(request, inspection_id):
    inspection = get_object_or_404(
        Inspection, pk=inspection_id,
        truck__company__created_by=request.user
    )
    truck = inspection.truck
    TireFS = inlineformset_factory(Inspection, Tire,
                                   form=TireFormSet.form,
                                   extra=0, can_delete=False)

    labels = gerar_posicoes_personalizadas(
        truck.truck_type.axle_count,
        truck.truck_type.tire_count
    )

    if request.method == "POST":
        form = InspectionForm(request.POST, instance=inspection)
        formset = TireFS(request.POST, instance=inspection)
        # reaplica labels
        for idx, tform in enumerate(formset.forms):
            tform.position_label = labels[idx]
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("core:inspection_detail", inspection_id=inspection.id)

    else:
        form = InspectionForm(instance=inspection)
        formset = TireFS(instance=inspection)
        for idx, tform in enumerate(formset.forms):
            tform.position_label = labels[idx]

    return render(request, "core/inspection_form.html", {
        "form": form,
        "formset": formset,
        "truck": truck,
    })


@login_required
def inspection_detail(request, inspection_id):
    inspection = get_object_or_404(
        Inspection, pk=inspection_id,
        truck__company__created_by=request.user
    )
    # lista de pneus ordenada
    tires = inspection.tires.all().order_by("position")
    # labels na mesma ordem
    tt = inspection.truck.truck_type
    labels = gerar_posicoes_personalizadas(tt.axle_count, tt.tire_count)

    tire_data = []
    for idx, tire in enumerate(tires):
        label = labels[idx] if idx < len(labels) else str(tire.position)
        # agora só há três sulcos:
        g1, g2, g3 = tire.groove_1, tire.groove_2, tire.groove_3
        # para o lado esquerdo (endswith "E") exibimos F-M-D (inverso),
        # para o direito mantemos D-M-F (original)
        if label.endswith("E"):
            grooves = [g3, g2, g1]  # Sulco F, M, D
        else:
            grooves = [g1, g2, g3]  # Sulco D, M, F
        tire_data.append((tire, label, grooves))

    return render(request, "core/inspection_detail.html", {
        "inspection": inspection,
        "tire_data": tire_data,
    })


@login_required
@require_POST
def inspection_delete(request, inspection_id):
    insp = get_object_or_404(
        Inspection, pk=inspection_id,
        truck__company__created_by=request.user
    )
    truck_id = insp.truck.id
    insp.delete()
    return redirect("core:inspection_list", truck_id=truck_id)
