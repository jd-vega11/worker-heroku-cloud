from django.shortcuts import render
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from django.middleware.csrf import get_token

# Cache
from django.core.cache import cache

# Authentication
from rest_framework.permissions import IsAuthenticated

# Helpers
from helpers import JsonMessageCreator

# Project and Design Model Imports
from projects.models import Projects, Designs
from projects.serializers import ProjectsSerializer, ProjectsPublicSerializer, CreateDesignsSerializer, GetBasicDesignsSerializer, GetDetailDesignsSerializer

# EnterpriseUser Model Imports
from projects.models import EnterpriseUser
from projects.serializers import EnterpriseUserSerializer
from projects.businessLogic import EnterpriseUserLogic

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def projectsIndexEnterprise(request, enterprise): 
    if request.method == 'GET':
        return projectsListEnterprise(request, enterprise)
    elif request.method == 'POST':
        return projectCreateEnterprise(request, enterprise)

@api_view(['GET'])
def projectsListPublic(request, enterprise):
    if f'{enterprise}_public' in cache:
        projects_serialized = ProjectsPublicSerializer(cache.get(f'{enterprise}_public'), many=True)
        return JsonResponse(projects_serialized.data, safe=False, status=status.HTTP_202_ACCEPTED)

    try: 
        user = EnterpriseUser.objects.get(company_id=enterprise)
    except:
        return JsonResponse(JsonMessageCreator.generateErrors([f'The enterprise={enterprise} could not be found.']), status=status.HTTP_404_NOT_FOUND)
    
    projects = Projects.objects.all().filter(owner=user.id)
    cache.set(f'{enterprise}_public', projects)
    projects_serialized = ProjectsPublicSerializer(projects, many=True)
    return JsonResponse(projects_serialized.data, safe=False)

def projectsListEnterprise(request, enterprise):
    if request.user.company_id != enterprise:
        return JsonResponse(JsonMessageCreator.generateErrors(['User cannot access that enterprise.']), status=status.HTTP_403_FORBIDDEN)
    
    projects = Projects.objects.all().filter(owner=request.user.id)
    projects_serialized = ProjectsSerializer(projects, many=True)
    return JsonResponse(projects_serialized.data, safe=False)

def projectCreateEnterprise(request, enterprise):
    if request.user.company_id != enterprise:
        return JsonResponse(JsonMessageCreator.generateErrors(['User cannot access that enterprise.']), status=status.HTTP_403_FORBIDDEN)

    project_data = JSONParser().parse(request)
    project_data['owner'] = request.user.id
    project_serialized = ProjectsSerializer(data=project_data)
    
    if project_serialized.is_valid():
        project_serialized.save()
        cache.delete(f'{enterprise}_public')
        return JsonResponse(project_serialized.data, status=status.HTTP_201_CREATED)
    return JsonResponse(project_serialized.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def projectDetailPrivate(request, enterprise, pk):
    if request.user.company_id != enterprise:
        return JsonResponse(JsonMessageCreator.generateErrors(['User cannot access that enterprise.']), status=status.HTTP_403_FORBIDDEN)

    try:
        project_data = Projects.objects.get(pk=pk)
        if project_data.owner.id != request.user.id:
            return JsonResponse(JsonMessageCreator.generateErrors(['Project does not belong to user']), status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            project_serialized = ProjectsSerializer(project_data)
            return JsonResponse(project_serialized.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            project_data.delete()
            cache.delete(f'{enterprise}_public')
            return JsonResponse({'msg': f'Project with id={pk} been deleted.'}, status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'PATCH':
            project_partial_data = JSONParser().parse(request) 
            project_serialized_partial = ProjectsSerializer(project_data, data=project_partial_data, partial=True)
            if project_serialized_partial.is_valid():
                project_serialized_partial.save()
                cache.delete(f'{enterprise}_public')
                return JsonResponse(project_serialized_partial.data, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(project_serialized_partial.errors, status=status.HTTP_400_BAD_REQUEST)

    except Projects.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def projectDetailPublic(request, enterprise, pk):
    try:
        user_owner = EnterpriseUser.objects.get(company_id=enterprise)
        project_data = Projects.objects.get(pk=pk)
        if project_data.owner.id != user_owner.id:
            return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            project_serialized = ProjectsPublicSerializer(project_data)
            return JsonResponse(project_serialized.data, status=status.HTTP_200_OK)

    except Projects.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)
    except EnterpriseUser.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Company not found']), status=status.HTTP_404_NOT_FOUND)
