from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import UserSerializer, LoginSerializer
from rest_framework.authtoken.models import Token
import logging
import json

# Configurar logging para debug
logger = logging.getLogger(__name__)

User = get_user_model()

@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['POST'])
def login(request):
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                # Gere ou recupere o token do usuário
                token, created = Token.objects.get_or_create(user=user)
                user_data = UserSerializer(user).data
                return Response({'token': token.key, **user_data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Credenciais inválidas.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    user = request.user
    return Response({
        'name': user.name,
        'email': user.email,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({'message': 'Logout bem-sucedido.'}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'error': 'Token não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Endpoint para solicitar recuperação de senha
    """
    try:
        # Debug: imprimir dados recebidos
        logger.info(f"Request body: {request.body}")
        logger.info(f"Request data: {request.data}")
        
        # Tentar pegar dados do request.data primeiro (DRF)
        if hasattr(request, 'data') and request.data:
            email = request.data.get('email')
        else:
            # Fallback para request.body
            data = json.loads(request.body)
            email = data.get('email')

        logger.info(f"Email recebido: {email}")

        if not email:
            return Response({
                'message': 'Email é obrigatório.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            logger.info(f"Usuário encontrado: {user.email}")
        except User.DoesNotExist:
            logger.info(f"Usuário não encontrado para email: {email}")
            # Por segurança, retornamos sucesso mesmo se o usuário não existir
            return Response({
                'message': 'Se o email existir em nossa base, você receberá instruções de recuperação.'
            }, status=status.HTTP_200_OK)
        
        # Gerar token de recuperação
        try:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            logger.info(f"Token gerado: {token[:10]}...")
            logger.info(f"UID gerado: {uid}")
        except Exception as e:
            logger.error(f"Erro ao gerar token: {str(e)}")
            return Response({
                'message': 'Erro interno do servidor.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # URL de redefinição
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
        reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"
        logger.info(f"Reset URL: {reset_url}")

        # Enviar email
        subject = 'Recuperação de Senha'
        
        # Versão em texto simples
        text_message = f'''Olá {user.first_name or user.username or 'Usuário'},

        Você solicitou a recuperação de sua senha.

        Clique no link abaixo para definir uma nova senha:
        {reset_url}

        Se você não solicitou esta recuperação, ignore este email.

        Este link expira em 24 horas.

        Atenciosamente,
        Equipe de Suporte'''

        try:
            # Verificar configurações de email
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            logger.info(f"Enviando email de: {from_email} para: {user.email}")
            
            # Para desenvolvimento, usar console backend se configurado
            email_backend = getattr(settings, 'EMAIL_BACKEND', '')
            logger.info(f"Email backend: {email_backend}")
            
            email_obj = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=[user.email]
            )

            email_obj.send()
            logger.info("Email enviado com sucesso")

            return Response({
                'message': 'Email de recuperação enviado com sucesso. Verifique sua caixa de entrada.'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            # Para desenvolvimento, ainda retornar sucesso se for console backend
            if 'console' in getattr(settings, 'EMAIL_BACKEND', ''):
                logger.info("Email backend é console, considerando como sucesso")
                return Response({
                    'message': 'Email de recuperação enviado com sucesso. Verifique sua caixa de entrada (console).'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'message': 'Erro ao enviar email. Tente novamente mais tarde.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro JSON: {str(e)}")
        return Response({
            'message': 'Dados inválidos.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erro geral: {str(e)}")
        return Response({
            'message': f'Erro interno do servidor: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    """
    Endpoint para confirmar a redefinição de senha
    """

    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.tokens import default_token_generator

    try:
        data = json.loads(request.body)
        uid = data.get('uid')
        token = data.get('token')
        new_password = data.get('new_password')

        if not all([uid, token, new_password]):
            return Response({
                'message': 'Todos os campos são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar senha
        if len(new_password) < 8:
            return Response({
                'message': 'A senha deve ter pelo menos 8 caracteres.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decodificar UID
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'message': 'Link inválido ou expirado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar token
        if not default_token_generator.check_token(user, token):
            return Response({
                'message': 'Link inválido ou expirado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Definir nova senha
        user.set_password(new_password)
        user.save()

        return Response({
            'message': 'Senha redefinida com sucesso!'
        }, status=status.HTTP_200_OK)
    
    except json.JSONDecodeError:
        return Response({
            'message': 'Dados inválidos.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'message': 'Erro interno do servidor.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

