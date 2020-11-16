from rest_framework import serializers
from projects.models import Projects, EnterpriseUser, Designs

class EnterpriseUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = EnterpriseUser
        fields = ('email', 'company_name', 'password', 'password_confirmation')

class ProjectsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Projects
        fields = ('id', 'name', 'description', 'cost', 'owner')

class ProjectsPublicSerializer(serializers.ModelSerializer):

    class Meta:
        model = Projects
        fields = ('id', 'name', 'description')

class CreateDesignsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Designs
        fields = ['design_uuid', 
        'designer_name', 
        'designer_lastname', 
        'designer_email', 
        'desing_original', 
        'design_price',
        'project',
        ]

class GetBasicDesignsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Designs
        fields = ['design_uuid', 
        'desing_original',
        'desing_converted',
        ]

class GetDetailDesignsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Designs
        fields = ['design_uuid', 
        'designer_name', 
        'designer_lastname', 
        'designer_email', 
        'design_state',   
        'desing_original',
        'desing_converted', 
        'design_price',
        'created_at',        
        ]