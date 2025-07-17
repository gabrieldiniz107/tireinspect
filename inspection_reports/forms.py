from django import forms
from datetime import date, timedelta

class MonthYearForm(forms.Form):
    start = forms.DateField(
        label="De (mês/ano)",
        input_formats=["%m/%Y"],
        widget=forms.TextInput(attrs={"placeholder": "MM/YYYY"}),
    )
    end = forms.DateField(
        label="Até (mês/ano)",
        input_formats=["%m/%Y"],
        widget=forms.TextInput(attrs={"placeholder": "MM/YYYY"}),
    )

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start"), cleaned.get("end")
        if start and end and start > end:
            raise forms.ValidationError("O mês inicial não pode ser maior que o final.")
        return cleaned

    def get_date_range(self):
        """Retorna (first_day, last_day) dos meses escolhidos."""
        start, end = self.cleaned_data["start"], self.cleaned_data["end"]
        # primeiro dia do mês
        first = date(start.year, start.month, 1)
        # último dia do mês final
        # para isso vamos avançar um mês e subtrair um dia
        if end.month == 12:
            next_month = date(end.year + 1, 1, 1)
        else:
            next_month = date(end.year, end.month + 1, 1)
        last = next_month - timedelta(days=1)
        return first, last
