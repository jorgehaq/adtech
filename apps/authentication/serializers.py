from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(default='user', required=False)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'tenant_id', 'role', 'password')
    
    def create(self, validated_data):
        # Asignar tenant por defecto si no se proporciona
        if 'tenant_id' not in validated_data:
            validated_data['tenant_id'] = 1
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            # Buscar el usuario por email
            user = User.objects.get(email=data['email'])
            # Verificar la contraseña
            if user.check_password(data['password']):
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled')
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError('Invalid credentials')
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid credentials')