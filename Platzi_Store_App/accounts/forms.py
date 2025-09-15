from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class CustomUserCreationForm(UserCreationForm):
    """
    Un formulario de creación de usuario personalizado que incluye
    email, nombre y apellido.
    """
    email = forms.EmailField(required=True, help_text='Requerido. Ingrese un correo electrónico válido.')
    first_name = forms.CharField(max_length=30, required=False, help_text='Opcional.')
    last_name = forms.CharField(max_length=150, required=False, help_text='Opcional.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')