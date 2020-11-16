from django.shortcuts import render
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes

# Authentication
from rest_framework.permissions import IsAuthenticated

# Helpers
from helpers import JsonMessageCreator

# EnterpriseUser Model Imports
from projects.models import EnterpriseUser
from projects.serializers import EnterpriseUserSerializer
from projects.businessLogic import EnterpriseUserLogic

@api_view(['POST'])
def userCreate(request):
    enterpriseUserData = JSONParser().parse(request)    

    if EnterpriseUserLogic().validatePasswordConfirmation(enterpriseUserData):
        return JsonResponse(JsonMessageCreator.generateErrors(['The provided passwords do not match.']), status=status.HTTP_406_NOT_ACCEPTABLE)

    enterpriseUserData = EnterpriseUserLogic().generateValidCompanyId(enterpriseUserData)
    
    try:
        EnterpriseUser.objects.create_user(
            email=enterpriseUserData['email'],
            company_name=enterpriseUserData['company_name'],
            company_id=enterpriseUserData['company_id'],
            password=enterpriseUserData['password'],
        )
        return JsonResponse(JsonMessageCreator.generateMessage('Successfully created user'), status=status.HTTP_201_CREATED)
    except Exception as e:
        return JsonResponse(JsonMessageCreator.generateErrors(['Could not create user', str(e)]), status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def userDelete(request, email):
    try:
        user = EnterpriseUser.objects.get(email=email)
    except EnterpriseUser.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateMessage(f'User with email={email} does not exist'), status=status.HTTP_404_NOT_FOUND)

    user.delete()
    return JsonResponse(JsonMessageCreator.generateMessage(f'User with email={email} has been deleted'), status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def companyInfo(request):    
    return JsonResponse(
        {
            'company_id': request.user.company_id,
            'company_name': request.user.company_name,
        }
        , status=status.HTTP_200_OK)
    