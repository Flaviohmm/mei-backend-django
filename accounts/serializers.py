from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'cnpj', 'password']

        extra_kwargs = {
            'password': {'write_only': True} # Torne a senha somente gravável
        }

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password']) # Chama o método de hashing
        user.save() # Salva o usuário
        return user
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Credenciais inválidas.")
        return data
    

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email é obrigatório.")
        return value
    

class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("A senha deve ter pelo menos 8 caracteres.")
        return value
