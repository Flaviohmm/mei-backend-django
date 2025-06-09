from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'cnpj', 'password']

        extra_kwargs = {
            'password': {'write_only': True} # Torne a senha somente gravável
        }

    def create(self, validated_data):
        # Salvar a senha de forma segura
        validated_data['password'] = make_password(validated_data['password'])
        user = User(**validated_data)
        user.save()
        return user