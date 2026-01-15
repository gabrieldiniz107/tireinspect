from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import ServiceOrder, ServiceOrderTruck
from core.models import Company
from django.db.models import Count, Q
from .forms import (
    ServiceOrderForm,
    ServiceOrderStep1Form,
    ServiceOrderStep2Form,
    ServiceItemsForm,
    TruckFormSet,
    TruckItemFormSet,
)
from django.http import HttpResponse
from .utils import gerar_pedido_pdf
import re


@login_required
def order_list(request):
    """Hub com cards de empresas do usuário e card de pedidos avulsos."""
    companies = (
        Company.objects.filter(created_by=request.user)
        .annotate(order_count=Count(
            "service_orders",
            filter=Q(service_orders__created_by=request.user, service_orders__is_draft=False),
        ))
        .order_by("name")
    )
    avulso_count = ServiceOrder.objects.filter(created_by=request.user, company__isnull=True, is_draft=False).count()
    return render(
        request,
        "service_orders/order_hub.html",
        {"companies": companies, "avulso_count": avulso_count},
    )


@login_required
def order_list_company(request, company_id):
    company = get_object_or_404(Company, pk=company_id, created_by=request.user)
    orders = ServiceOrder.objects.filter(created_by=request.user, company=company, is_draft=False)
    return render(
        request,
        "service_orders/order_list_filtered.html",
        {
            "orders": orders,
            "title": f"Pedidos — {company.name}",
            "subtitle": company.cnpj or "",
            "new_order_for_company": company,
        },
    )


@login_required
def order_list_avulso(request):
    orders = ServiceOrder.objects.filter(created_by=request.user, company__isnull=True, is_draft=False)
    return render(
        request,
        "service_orders/order_list_filtered.html",
        {
            "orders": orders,
            "title": "Pedidos Avulsos",
            "subtitle": "Pedidos sem empresa vinculada",
            "new_order_avulso": True,
        },
    )


@login_required
def order_create(request):
    """Etapa 1: Data do pedido (número removido)."""
    if request.method == "POST":
        form = ServiceOrderStep1Form(request.POST)
    else:
        from django.utils import timezone
        form = ServiceOrderStep1Form(initial={"order_date": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        request.session["order_step1"] = {
            "order_date": str(form.cleaned_data["order_date"]),
        }
        return redirect("service_orders:order_create_step2")
    return render(request, "service_orders/order_wizard.html", {"form": form})


@login_required
def order_create_step2(request):
    """Etapa 2: Cliente, CNPJ/CPF e caminhões (placa/frota)."""
    step1 = request.session.get("order_step1") or {}
    if not step1:
        return redirect("service_orders:order_create")

    # Verificar se veio de um card (empresa travada ou avulso)
    locked_company_id = request.session.get("order_company_id", "__unset__")
    lock_company = locked_company_id != "__unset__"
    fixed_company = None
    if lock_company and locked_company_id:
        fixed_company = get_object_or_404(Company, pk=locked_company_id, created_by=request.user)

    if request.method == "POST":
        form = ServiceOrderStep2Form(request.POST)
        form.fields["company"].queryset = Company.objects.filter(created_by=request.user)
        formset = TruckFormSet(request.POST, queryset=ServiceOrderTruck.objects.none())
        if form.is_valid() and formset.is_valid():
            truck_count = form.cleaned_data.get("truck_count") or 1
            company = fixed_company if lock_company else form.cleaned_data.get("company")
            order = ServiceOrder(
                created_by=request.user,
                order_date=step1.get("order_date"),
                company=company,
                client=(company.name if company else form.cleaned_data["client"]),
                cnpj_cpf=(company.cnpj if company else form.cleaned_data["cnpj_cpf"]),
                is_draft=True,
            )
            order.save()

            # Salvar apenas os primeiros 'truck_count' forms com conteúdo relevante
            saved = 0
            for idx, f in enumerate(formset.forms):
                if saved >= truck_count:
                    break
                if not f.cleaned_data:
                    continue
                # Considera como 'preenchido' se houver placa, frota, observação ou valor da observação
                has_content = any([
                    (f.cleaned_data.get("plate") or "").strip(),
                    (f.cleaned_data.get("fleet") or "").strip(),
                    (f.cleaned_data.get("observation") or "").strip(),
                    f.cleaned_data.get("observation_price") is not None,
                ])
                if not has_content:
                    continue
                truck = f.save(commit=False)
                truck.order = order
                if truck.fleet is None:
                    truck.fleet = ""
                if truck.plate is None:
                    truck.plate = ""
                truck.save()
                # Observações adicionais: capturar arrays do POST por índice do form
                texts = request.POST.getlist(f'extra_obs-{idx}-text[]')
                prices = request.POST.getlist(f'extra_obs-{idx}-price[]')
                if texts or prices:
                    from .models import ServiceOrderTruckObservation
                    for i, txt in enumerate(texts or []):
                        txt_norm = (txt or "").strip()
                        price_val = None
                        if i < len(prices):
                            try:
                                pv = prices[i]
                                price_val = None if pv in ("", None) else float(pv)
                            except Exception:
                                price_val = None
                        if not txt_norm and price_val is None:
                            continue
                        ServiceOrderTruckObservation.objects.create(
                            truck=truck,
                            content=txt_norm,
                            price=price_val,
                        )
                saved += 1

            request.session.pop("order_step1", None)
            if lock_company:
                request.session.pop("order_company_id", None)
            return redirect("service_orders:order_create_step3", order_id=order.id)
    else:
        initial = {}
        if fixed_company:
            initial["company"] = fixed_company
        form = ServiceOrderStep2Form(initial=initial)
        form.fields["company"].queryset = Company.objects.filter(created_by=request.user)
        # Passa a data do step1 como inicial para cada form de caminhão
        order_date = step1.get("order_date")
        truck_initial = [{"date": order_date} for _ in range(10)]
        formset = TruckFormSet(queryset=ServiceOrderTruck.objects.none(), initial=truck_initial)

    companies = Company.objects.filter(created_by=request.user)
    companies_data = [{"id": c.id, "name": c.name, "cnpj": c.cnpj} for c in companies]
    # Garante que order_date esteja definido para o template
    order_date = step1.get("order_date", "")
    return render(
        request,
        "service_orders/order_step2.html",
        {
            "form": form,
            "formset": formset,
            "companies": companies,
            "companies_data": companies_data,
            "fixed_company": fixed_company,
            "lock_company": lock_company,
            "order_date": order_date,
        },
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(ServiceOrder, pk=order_id, created_by=request.user)
    # Se ainda é rascunho, redireciona para a etapa de serviços (passo 3) para finalizar
    if getattr(order, "is_draft", False):
        return redirect("service_orders:order_create_step3", order_id=order.id)
    trucks = order.trucks.all().prefetch_related("items", "observations")
    unassigned = order.items.filter(truck__isnull=True)
    return render(request, "service_orders/order_detail.html", {"order": order, "trucks": trucks, "unassigned_items": unassigned})


@login_required
def order_create_step3(request, order_id):
    """Etapa 3: Serviços por caminhão (tipo, quantidade, valor)."""
    order = get_object_or_404(ServiceOrder, pk=order_id, created_by=request.user)

    trucks = list(order.trucks.all())
    formsets = []
    all_valid = True

    if request.method == "POST":
        for t in trucks:
            fs = TruckItemFormSet(request.POST, instance=t, prefix=f"truck_{t.id}")
            valid = fs.is_valid()
            all_valid = all_valid and valid
            formsets.append((t, fs))
        if all_valid:
            for _, fs in formsets:
                fs.save()
            # Salvar descontos por caminhão (campo simples fora do formset)
            from decimal import Decimal, InvalidOperation
            for t, _ in formsets:
                key = f"discount-{t.id}"
                raw = request.POST.get(key)
                try:
                    t.discount = None if raw in (None, "") else Decimal(str(raw))
                except (InvalidOperation, Exception):
                    t.discount = t.discount  # mantém o valor atual se inválido
                t.save(update_fields=["discount", "updated_at"]) if hasattr(t, "updated_at") else t.save(update_fields=["discount"]) 
            # Finaliza o pedido ao salvar os serviços
            if getattr(order, "is_draft", False):
                order.is_draft = False
                order.save(update_fields=["is_draft"])
            return redirect("service_orders:order_detail", order_id=order.id)
    else:
        for t in trucks:
            fs = TruckItemFormSet(instance=t, prefix=f"truck_{t.id}")
            formsets.append((t, fs))

    return render(request, "service_orders/order_step3.html", {"order": order, "truck_formsets": formsets})


@login_required
def order_pdf(request, order_id):
    order = get_object_or_404(ServiceOrder, pk=order_id, created_by=request.user)
    pdf_bytes = gerar_pedido_pdf(order)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    # Build default filename: <EmpresaOuCliente>__pedido_<NumeroOuID>__<Data>.pdf
    company_or_client = (order.company.name if order.company else order.client) or "Empresa"
    num = order.service_number or str(order.id)
    date_str = order.order_date.isoformat()
    default_name = f"{company_or_client}__pedido_{num}__{date_str}.pdf"
    # Sanitize helper (duplicate minimal logic to avoid import cycle)
    _SAFE_CHARS_RE = re.compile(r"[^A-Za-z0-9._\- ]+")
    def _sanitize(name: str, default: str) -> str:
        name = (name or "").strip()
        if not name:
            return default
        name = name.replace("/", "_").replace("\\", "_").replace("\0", "_")
        name = _SAFE_CHARS_RE.sub("_", name)
        name = re.sub(r"\s+", " ", name).strip()
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        return name
    requested = request.GET.get("filename")
    filename = _sanitize(requested, default_name)
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@login_required
def order_delete(request, order_id):
    order = get_object_or_404(ServiceOrder, pk=order_id, created_by=request.user)
    if request.method == "POST":
        order.delete()
        return redirect("service_orders:order_list")
    # For non-POST, just redirect to detail to avoid accidental deletes
    return redirect("service_orders:order_detail", order_id=order.id)


# ---------- Edit flow ----------

@login_required
def order_edit_step1(request, order_id):
    order = get_object_or_404(ServiceOrder, pk=order_id, created_by=request.user)
    form = ServiceOrderStep1Form(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("service_orders:order_edit_step2", order_id=order.id)
    return render(request, "service_orders/order_wizard.html", {"form": form, "is_edit": True, "order": order})


@login_required
def order_edit_step2(request, order_id):
    order = get_object_or_404(ServiceOrder, pk=order_id, created_by=request.user)
    initial_count = order.trucks.count() or 1

    if request.method == "POST":
        form = ServiceOrderStep2Form(request.POST, instance=order)
        form.fields["company"].queryset = Company.objects.filter(created_by=request.user)
        formset = TruckFormSet(request.POST, queryset=order.trucks.all())
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            company = form.cleaned_data.get("company")
            if company:
                obj.client = company.name
                obj.cnpj_cpf = company.cnpj
            obj.save()
            n = form.cleaned_data.get("truck_count") or initial_count
            saved_ids = []
            # Save up to n
            for idx, f in enumerate(formset.forms):
                if idx >= n:
                    break
                if not f.cleaned_data:
                    continue
                obj = f.save(commit=False)
                if not getattr(obj, "order_id", None):
                    obj.order = order
                # Conteúdo relevante além da data (que é padrão)
                has_content = any([
                    (f.cleaned_data.get("plate") or "").strip(),
                    (f.cleaned_data.get("fleet") or "").strip(),
                    (f.cleaned_data.get("observation") or "").strip(),
                    f.cleaned_data.get("observation_price") is not None,
                ])
                if has_content:
                    if obj.fleet is None:
                        obj.fleet = ""
                    if obj.plate is None:
                        obj.plate = ""
                    obj.save()
                    # Recriar observações adicionais a partir do POST
                    texts = request.POST.getlist(f'extra_obs-{idx}-text[]')
                    prices = request.POST.getlist(f'extra_obs-{idx}-price[]')
                    from .models import ServiceOrderTruckObservation
                    # Limpa existentes e recria conforme o post atual
                    obj.observations.all().delete()
                    if texts or prices:
                        for i, txt in enumerate(texts or []):
                            txt_norm = (txt or "").strip()
                            price_val = None
                            if i < len(prices):
                                try:
                                    pv = prices[i]
                                    price_val = None if pv in ("", None) else float(pv)
                                except Exception:
                                    price_val = None
                            if not txt_norm and price_val is None:
                                continue
                            ServiceOrderTruckObservation.objects.create(
                                truck=obj,
                                content=txt_norm,
                                price=price_val,
                            )
                    saved_ids.append(obj.id)
            # remove extras beyond n
            order.trucks.exclude(id__in=saved_ids).delete()
            return redirect("service_orders:order_edit_step3", order_id=order.id)
    else:
        form = ServiceOrderStep2Form(instance=order, initial={"truck_count": initial_count})
        form.fields["company"].queryset = Company.objects.filter(created_by=request.user)
        formset = TruckFormSet(queryset=order.trucks.all())

    companies = Company.objects.filter(created_by=request.user)
    companies_data = [{"id": c.id, "name": c.name, "cnpj": c.cnpj} for c in companies]
    return render(request, "service_orders/order_step2.html", {"form": form, "formset": formset, "is_edit": True, "order": order, "companies": companies, "companies_data": companies_data})


@login_required
def order_edit_step3(request, order_id):
    order = get_object_or_404(ServiceOrder, pk=order_id, created_by=request.user)

    trucks = list(order.trucks.all())
    formsets = []
    all_valid = True

    if request.method == "POST":
        for t in trucks:
            fs = TruckItemFormSet(request.POST, instance=t, prefix=f"truck_{t.id}")
            valid = fs.is_valid()
            all_valid = all_valid and valid
            formsets.append((t, fs))
        if all_valid:
            for _, fs in formsets:
                fs.save()
            # Atualizar descontos por caminhão
            from decimal import Decimal, InvalidOperation
            for t, _ in formsets:
                key = f"discount-{t.id}"
                raw = request.POST.get(key)
                try:
                    t.discount = None if raw in (None, "") else Decimal(str(raw))
                except (InvalidOperation, Exception):
                    pass
                t.save(update_fields=["discount"]) 
            return redirect("service_orders:order_detail", order_id=order.id)
    else:
        for t in trucks:
            fs = TruckItemFormSet(instance=t, prefix=f"truck_{t.id}")
            formsets.append((t, fs))

    return render(request, "service_orders/order_step3.html", {"order": order, "truck_formsets": formsets, "is_edit": True})


@login_required
def order_create_for_company(request, company_id):
    company = get_object_or_404(Company, pk=company_id, created_by=request.user)
    request.session["order_company_id"] = company.id
    return redirect("service_orders:order_create")


@login_required
def order_create_avulso(request):
    # Define chave presente porém com valor falsy para travar avulso
    request.session["order_company_id"] = None
    return redirect("service_orders:order_create")
