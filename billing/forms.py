from django import forms

from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'paid_on']
        widgets = {'paid_on': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, enrollment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.enrollment = enrollment
        self.fields['payment_method'].choices = [
            ('CASH', 'Cash'), ('FONEPAY', 'Fonepay'), ('Cash', 'Cash'), ('Fonepay', 'Fonepay'),
        ]

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Payment amount must be greater than zero.')
        if self.enrollment and amount > self.enrollment.balance_due:
            raise forms.ValidationError('Payment cannot exceed the outstanding balance.')
        return amount

    def clean_payment_method(self):
        method = self.cleaned_data['payment_method']
        return {'Cash': 'CASH', 'Fonepay': 'FONEPAY'}.get(method, method)