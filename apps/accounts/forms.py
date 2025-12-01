# apps/accounts/forms.py

"""
Forms for Accounts App
"""

from django import forms
from django.core.validators import RegexValidator
from .models import User


class PhoneForm(forms.Form):
    """فرم دریافت شماره موبایل"""
    
    phone = forms.CharField(
        max_length=15,
        min_length=10,
        label='شماره موبایل',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '۰۹۱۲۳۴۵۶۷۸۹',
            'dir': 'ltr',
            'inputmode': 'numeric',
            'autocomplete': 'tel',
            'autofocus': True,
        }),
        error_messages={
            'required': 'شماره موبایل را وارد کنید',
            'min_length': 'شماره موبایل نامعتبر است',
            'max_length': 'شماره موبایل نامعتبر است',
        }
    )
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        
        # Import normalize function
        from .views import normalize_phone
        
        normalized = normalize_phone(phone)
        if not normalized:
            raise forms.ValidationError('شماره موبایل نامعتبر است')
        
        return normalized


class OTPForm(forms.Form):
    """فرم دریافت کد OTP"""
    
    code = forms.CharField(
        max_length=6,
        min_length=4,
        label='کد تایید',
        widget=forms.TextInput(attrs={
            'class': 'form-input otp-input',
            'placeholder': '- - - - -',
            'dir': 'ltr',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'autofocus': True,
            'maxlength': '5',
        }),
        error_messages={
            'required': 'کد تایید را وارد کنید',
            'min_length': 'کد تایید نامعتبر است',
        }
    )
    
    def clean_code(self):
        code = self.cleaned_data['code']
        
        # Only digits allowed
        if not code.isdigit():
            raise forms.ValidationError('کد تایید باید فقط شامل اعداد باشد')
        
        return code


class ProfileForm(forms.ModelForm):
    """فرم ویرایش پروفایل"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'نام',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'نام خانوادگی',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'ایمیل (اختیاری)',
                'dir': 'ltr',
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if email:
            # Check uniqueness
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('این ایمیل قبلاً استفاده شده است')
        
        return email or None
