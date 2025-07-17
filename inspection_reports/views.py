# inspection_reports/views.py
from datetime import date
from calendar import monthrange
import re

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from core.models import Inspection, Company  # ajuste se Company estiver em outro app


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
_MMYYYY_RE = re.compile(r"^(0[1-9]|1[0-2])/[0-9]{4}$")  # 01/2024 … 12/2099


def _month_start(d: date) -> date:
    """Primeiro dia do mês."""
    return date(d.year, d.month, 1)


def _month_end(d: date) -> date:
    """Último dia do mês."""
    last = monthrange(d.year, d.month)[1]
    return date(d.year, d.month, last)


def _str_to_month(raw: str) -> date:
    """Converte 'MM/YYYY' para date(YYYY, MM, 1)."""
    mes, ano = map(int, raw.split("/"))
    return date(ano, mes, 1)


# --------------------------------------------------------------------------- #
# Formulário
# --------------------------------------------------------------------------- #
class MonthRangeForm(forms.Form):
    start = forms.CharField(
        label=_("Mês inicial (MM/AAAA)"),
        widget=forms.TextInput(attrs={"placeholder": "07/2025"}),
    )
    end = forms.CharField(
        label=_("Mês final (MM/AAAA)"),
        widget=forms.TextInput(attrs={"placeholder": "09/2025"}),
    )
    company = forms.ModelChoiceField(
        label=_("Empresa (opcional)"),
        queryset=Company.objects.none(),
        required=False,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["company"].queryset = Company.objects.filter(created_by=user)

    # --- campos individuais ---
    def clean_start(self):
        raw = self.cleaned_data["start"].strip()
        if not _MMYYYY_RE.match(raw):
            raise ValidationError(_("Use o formato MM/AAAA."))
        return _str_to_month(raw)  # retorna date(YYYY, MM, 1)

    def clean_end(self):
        raw = self.cleaned_data["end"].strip()
        if not _MMYYYY_RE.match(raw):
            raise ValidationError(_("Use o formato MM/AAAA."))
        d = _str_to_month(raw)
        return _month_end(d)  # retorna date(YYYY, MM, último dia)

    # --- validação cruzada ---
    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start")
        end = cleaned.get("end")
        if start and end and start > end:
            self.add_error("end", _("O mês final deve ser igual ou posterior ao inicial."))
        return cleaned


# --------------------------------------------------------------------------- #
# View
# --------------------------------------------------------------------------- #
@login_required
def report_by_month_range(request):
    """
    Exibe o formulário e, se válido, lista as inspeções no intervalo escolhido.
    """
    form = MonthRangeForm(request.GET or None, user=request.user)
    inspections = None  # template decide o que mostrar

    if form.is_valid():
        start_date = form.cleaned_data["start"]  # já é date(...)
        end_date = form.cleaned_data["end"]      # idem
        company = form.cleaned_data.get("company")

        qs = (
            Inspection.objects.filter(
                date__range=(start_date, end_date),
                truck__company__created_by=request.user,
            )
            .select_related("truck", "truck__company")
            .order_by("-date")
        )

        if company:
            qs = qs.filter(truck__company=company)

        inspections = qs

    context = {
        "form": form,
        "inspections": inspections,  # pode ser None
    }
    return render(request, "inspection_reports/report_by_month.html", context)
