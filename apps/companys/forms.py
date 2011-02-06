from django import forms
from django.utils.translation import ugettext_lazy as _

from companys.models import Company

# @@@ we should have auto slugs, even if suggested and overrideable

class CompanyForm(forms.ModelForm):
    
    slug = forms.SlugField(max_length=20,
        help_text = _("a short version of the name consisting only of letters, numbers, underscores and hyphens."),)
        #error_message = _("This value must contain only letters, numbers, underscores and hyphens."))
            
    domain = forms.CharField(
        max_length=20,
        help_text = _("company domain name, e.g. google.com."))

    def clean_domain(self):
        if Company.objects.filter(domain__iexact=self.cleaned_data["domain"]).count() > 0:
            raise forms.ValidationError(_("A company already exists with that domain."))
        return self.cleaned_data["domain"]

    location = forms.CharField(
        required = False,
        max_length = 100,
        help_text = _("company address."))

    zipcode = forms.CharField(
        required = False,
        min_length = 5,
        max_length = 5,
        help_text = _("zip code."))

    website = forms.URLField(
        required = False,
        verify_exists = True,
        help_text = _("company website url."))

    logo = forms.URLField(
        required = False,
        verify_exists = True,
        help_text = _("company logo url."))
            
    def clean_slug(self):
        if Company.objects.filter(slug__iexact=self.cleaned_data["slug"]).count() > 0:
            raise forms.ValidationError(_("A company already exists with that slug."))
        return self.cleaned_data["slug"].lower()
    
    def clean_name(self):
        if Company.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
            raise forms.ValidationError(_("A company already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Company
        fields = ('name', 'slug', 'description', 'domain', 'location', 'zipcode', 'website', 'logo')


# @@@ is this the right approach, to have two forms where creation and update fields differ?

class CompanyUpdateForm(forms.ModelForm):
    
    def clean_name(self):
        if Company.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
            if self.cleaned_data["name"] == self.instance.name:
                pass # same instance
            else:
                raise forms.ValidationError(_("A company already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Company
        fields = ('name', 'description', 'domain', 'location', 'zipcode', 'website', 'logo')
