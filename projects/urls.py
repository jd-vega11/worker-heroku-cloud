from django.urls import path
from projects.views import viewsDesigns, viewsProjects, viewsUsers
from django.conf.urls import url
from rest_framework.authtoken import views as views_auth

urlpatterns = [
    # Public endpoints
    path('<enterprise>/projects/', viewsProjects.projectsListPublic),
    path('<enterprise>/projects/<int:pk>', viewsProjects.projectDetailPublic),
    path('<enterprise>/projects/<int:project_id>/designs/', viewsDesigns.designsListPublic),
    path('<enterprise>/projects/<int:project_id>/designs/default/', viewsDesigns.designsCreateDefault),
    
    # Login
    path('enterprise-users/login/', views_auth.obtain_auth_token),
    
    # EnterpriseUser
    path('enterprise-users/', viewsUsers.userCreate),
    path('enterprise-users/my-company-info/', viewsUsers.companyInfo),
    path('enterprise-users/<email>/', viewsUsers.userDelete),
    
    # Enterprise endpoints
    path('enterprise/<enterprise>/projects/', viewsProjects.projectsIndexEnterprise),
    path('enterprise/<enterprise>/projects/<int:pk>', viewsProjects.projectDetailPrivate),
    
    # Design endpoints
    path('enterprise/<enterprise>/projects/<int:project_id>/designs/', viewsDesigns.designsListPrivate),
    path('enterprise/<enterprise>/projects/<int:project_id>/designs/<design_uuid>', viewsDesigns.designsDetailPrivate),
]