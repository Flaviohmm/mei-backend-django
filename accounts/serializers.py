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
    