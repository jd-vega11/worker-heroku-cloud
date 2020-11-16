from django.http.response import JsonResponse
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.pagination import PageNumberPagination

# Authentication
from rest_framework.permissions import IsAuthenticated

# Helpers
from helpers import JsonMessageCreator

# Project and Design Model Imports
from projects.models import Projects, Designs
from projects.serializers import CreateDesignsSerializer, GetBasicDesignsSerializer, GetDetailDesignsSerializer

# EnterpriseUser Model Imports
from projects.models import EnterpriseUser

#Default Image Management
import uuid
import os
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from projects.tasks import processDesigns


@api_view(['GET','POST'])
@parser_classes([MultiPartParser])
def designsListPublic(request, enterprise, project_id):
    try:
        user_owner = EnterpriseUser.objects.get(company_id=enterprise)
        project_data = Projects.objects.get(pk=project_id)
        if project_data.owner.id != user_owner.id:
            return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            designs = Designs.objects.filter(project=project_id, design_state='DISPONIBLE')            
            paginator = PageNumberPagination()
            paginator.page_size = 10            
            designs_page = paginator.paginate_queryset(designs, request)
            designs_serializer = GetBasicDesignsSerializer(designs_page, many = True)
            desings_response = paginator.get_paginated_response(designs_serializer.data)
            return desings_response
        elif request.method == 'POST':
            designs_data = request.data.copy()
            designs_data['project'] = project_id
            designs_serializer = CreateDesignsSerializer(data=designs_data)
            if designs_serializer.is_valid():
                designs_serializer.save()
                print(designs_serializer.data["design_uuid"])
                processDesigns.delay(designs_serializer.data["design_uuid"])
                return JsonResponse(designs_serializer.data, status=status.HTTP_201_CREATED)

            return JsonResponse(designs_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Projects.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)
    except EnterpriseUser.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Company not found']), status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse(JsonMessageCreator.generateErrors(['Internal server error']), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser])
def designsCreateDefault(request, enterprise, project_id):
    try:
        user_owner = EnterpriseUser.objects.get(company_id=enterprise)
        project_data = Projects.objects.get(pk=project_id)
        if project_data.owner.id != user_owner.id:
            return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'POST':
            designs_data = request.data.copy()

            #Assign project id
            designs_data['project'] = project_id

            #Generate default image
            original_path = os.path.join(settings.BASE_DIR, 'projects/static/test/defaultimage.jpeg')
            with open(original_path, 'rb') as image:
                thumb_io = BytesIO(image.read())

                filename = '{}.{}'.format(uuid.uuid4().hex, 'jpeg')
                thumb_io.name = filename

                image_field_file = InMemoryUploadedFile(thumb_io, None, filename, "image/jpeg", thumb_io.getbuffer().nbytes, None)
   
                #Assign default design
                designs_data['desing_original'] = image_field_file

            designs_serializer = CreateDesignsSerializer(data=designs_data)
            if designs_serializer.is_valid():
                designs_serializer.save()
                print(designs_serializer.data["design_uuid"])
                processDesigns.delay(designs_serializer.data["design_uuid"])
                return JsonResponse(designs_serializer.data, status=status.HTTP_201_CREATED)

            return JsonResponse(designs_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Projects.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)
    except EnterpriseUser.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Company not found']), status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def designsListPrivate(request, enterprise, project_id):
    if request.user.company_id != enterprise:
        return JsonResponse(JsonMessageCreator.generateErrors(['User cannot access that enterprise.']), status=status.HTTP_403_FORBIDDEN)

    try:
        project_data = Projects.objects.get(pk=project_id)
        if project_data.owner.id != request.user.id:
            return JsonResponse(JsonMessageCreator.generateErrors(['Project does not belong to user']), status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            designs = Designs.objects.filter(project=project_id, design_state='DISPONIBLE')            
            paginator = PageNumberPagination()
            paginator.page_size = 10            
            designs_page = paginator.paginate_queryset(designs, request)
            designs_serializer = GetDetailDesignsSerializer(designs_page, many = True)
            desings_response = paginator.get_paginated_response(designs_serializer.data)
            return desings_response

    except Projects.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def designsDetailPrivate(request, enterprise, project_id, design_uuid):
    if request.user.company_id != enterprise:
        return JsonResponse(JsonMessageCreator.generateErrors(['User cannot access that enterprise.']), status=status.HTTP_403_FORBIDDEN)

    try:
        project_data = Projects.objects.get(pk=project_id)
        if project_data.owner.id != request.user.id:
            return JsonResponse(JsonMessageCreator.generateErrors(['Project does not belong to user']), status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            design = Designs.objects.get(design_uuid = design_uuid, project=project_id)
            desigs_serializer = GetDetailDesignsSerializer(design)
            return JsonResponse(desigs_serializer.data, status=status.HTTP_200_OK)
       
    except Projects.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Project not found']), status=status.HTTP_404_NOT_FOUND)
    except Designs.DoesNotExist:
        return JsonResponse(JsonMessageCreator.generateErrors(['Design not found']), status=status.HTTP_404_NOT_FOUND)