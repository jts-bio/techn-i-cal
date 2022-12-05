from django import forms 



class LoginForm (forms.Form):
    username = forms.CharField(widget=forms.TextInput, 
                                max_length=128,
                                label='Username')
    password = forms.CharField(widget=forms.PasswordInput, 
                                max_length=40,
                                label='Password')   


    