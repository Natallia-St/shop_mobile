from django import forms
from django.contrib.auth import get_user_model
from .models import Order, Review

# Mетод вернет текущую активную модель пользователя
User = get_user_model()


class OrderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # Вызываем  метод инициализации из родительского класса forms.ModelForm, чтобы дополнить его - изменяем
        # поле про дату заказа - добавляем в нее календарь с возможностью выбора в нем даты .
        super().__init__(*args, **kwargs)
        self.fields['order_date'].label = 'Дата получения заказа'

    order_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

    # Определяем, какая модель будет использоваться для создании формы, какие поля будут в форме
    class Meta:
        model = Order
        fields = (
            'first_name', 'last_name', 'phone', 'address', 'buying_type', 'order_date', 'comment'
        )


class LoginForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']
    # Вызываем  метод инициализации из родительского класса forms.ModelForm, чтобы дополнить его - изменяем
    # имя полей.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError(f'Пользователь с логином "{username} не найден в системе')
        user = User.objects.filter(username=username).first()
        if user:
            if not user.check_password(password):
                raise forms.ValidationError("Неверный пароль")
        return self.cleaned_data


class RegistrationForm(forms.ModelForm):

    confirm_password = forms.CharField(widget=forms.PasswordInput)
    password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(required=False)
    address = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
        self.fields['confirm_password'].label = 'Подтвердите пароль'
        self.fields['phone'].label = 'Номер телефона'
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['address'].label = 'Адрес'
        self.fields['email'].label = 'Электронная почта'

    def clean_email(self):
        email = self.cleaned_data['email']
        # domain = email.split('.')[-1]
        # if domain in ['com', 'net']:
        #     raise forms.ValidationError(
        #         f'Регистрация для домена {domain} невозможна'
        #     )
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                f'Данный почтовый адрес уже зарегистрирован в системе'
            )
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                f'Имя {username} занято'
            )
        return username

    def clean(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise forms.ValidationError('Пароли не совпадают')
        return self.cleaned_data

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'first_name', 'last_name', 'address', 'phone', 'email']


class ReviewForm(forms.ModelForm):

    title = forms.CharField(required=True, max_length=60, widget=forms.TextInput(attrs={"class": "form-control"}))
    name_user= forms.CharField(required=True, max_length=60, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(required=True, max_length=60, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, max_length=60, widget=forms.TextInput(attrs={"class": "form-control"}))
    describe = forms.CharField(required=True, widget=forms.Textarea(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Краткое содержание обращения'
        self.fields['name_user'].label = 'Организация/Имя/Фамилия'
        self.fields['phone'].label = 'Номер телефона'
        self.fields['email'].label = 'Электронная почта'
        self.fields['describe'].label = 'Текст обращения'



    class Meta:
        model = Review
        fields = ['title', 'name_user', 'phone', 'email', 'describe',]
