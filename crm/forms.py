from django import forms
from .models import Doctor, Appointment, VisitReport, Organization

class DoctorForm(forms.ModelForm):
    def save(self, commit=True, *args, **kwargs):
        obj = super().save(commit=False)
        request = kwargs.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            if getattr(obj, 'owner_id', None) is None:
                obj.owner = request.user
        if commit:
            obj.save()
            try:
                self.save_m2m()
            except Exception:
                pass
        return obj

    class Meta:
        model = Doctor
        fields = ['name','crm','uf','specialty','email','phone','notes']
        widgets = {k: forms.TextInput(attrs={'class':'form-control'}) for k in ['name','crm','uf','specialty','email','phone']}
        widgets.update({'notes': forms.Textarea(attrs={'class':'form-control', 'rows':3})})


    def clean(self):
        data = super().clean()
        name = (data.get('name') or '').strip()
        crm  = (data.get('crm') or '').strip()
        if name and crm:
            from django.db.models.functions import Lower
            qs = Doctor.objects.annotate(name_l=Lower('name')).filter(name_l=name.lower(), crm=crm)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Já existe um médico com este Nome e CRM.')
        return data

class AppointmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            try:
                from .models import Representative
                rep, _ = Representative.objects.get_or_create(user=request.user)
                qs = Doctor.objects.filter(assignments__representative=rep, assignments__active=True).distinct()
                self.fields['doctor'].queryset = qs
            except Exception:
                pass

    when = forms.DateTimeField(label='Data e Hora', widget=forms.DateTimeInput(attrs={'type':'datetime-local','class':'form-control'}))
    class Meta:
        model = Appointment
        fields = ['doctor','contact_name','when','status','notes']
        widgets = {
            'doctor': forms.Select(attrs={'class':'form-select'}),
            'contact_name': forms.TextInput(attrs={'class':'form-control'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'notes': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
        }

class VisitReportForm(forms.ModelForm):
    class Meta:
        model = VisitReport
        fields = ['visit_number','mode','objective','summary','outcome','next_steps']
        widgets = {
            'visit_number': forms.Select(attrs={'class':'form-select'}),
            'mode': forms.Select(attrs={'class':'form-select'}),
            'objective': forms.TextInput(attrs={'class':'form-control'}),
            'summary': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
            'outcome': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
            'next_steps': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
        }
