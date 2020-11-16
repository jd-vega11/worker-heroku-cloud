from django.db import models
from django.utils import timezone
import uuid
import os
from django.utils.deconstruct import deconstructible
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from PIL import Image
from django.core.files.images import get_image_dimensions
from io import BytesIO

# Create your models here.
class EnterpriseUserManager(BaseUserManager):
    def create_user(self, email, company_name, company_id, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            company_name=company_name,
            company_id=company_id,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, company_name, company_id, password=None):
        user = self.model(
            email=self.normalize_email(email),
            company_name=company_name,
            company_id=company_id,
        )
        user.is_admin = True
        user.set_password(password)
        user.save(using=self._db)
        return user

class EnterpriseUser(AbstractBaseUser):
    email = models.EmailField(max_length=100, unique=True)
    company_name = models.CharField(max_length=100, blank=False, default='')
    company_id = models.CharField(max_length=100, blank=False, default='', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['company_name', 'company_id']
    
    objects = EnterpriseUserManager()

class Projects(models.Model):
    name = models.CharField(max_length=50, blank=False, default='')
    description = models.CharField(max_length=1000, blank=False, default='')
    cost = models.DecimalField(max_digits=100, decimal_places=0)
    owner = models.ForeignKey(EnterpriseUser, on_delete=models.CASCADE)

# Generate tokens for the users model
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@deconstructible
class PathAndRename(object):

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # set filename as random string
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)

path_original_image = PathAndRename("designs/original")
path_converted_image = PathAndRename("designs/converted")

@deconstructible
class ResolutionAndType(object):

    def __init__(self, width=None, height=None):
        self.width = width
        self.height = height

    def __call__(self, image):        

        errors = []

        # validate the resolution of the uploaded image  
        w, h = get_image_dimensions(image)    

        if self.width is not None and w < self.width:
            errors.append('Design width should be >= {} px.'.format(self.width))
        if self.height is not None and h < self.height:
            errors.append('Design height should be >= {} px.'.format(self.height))

        # Validate image type
        if hasattr(image, 'temporary_file_path'):
            file = image.temporary_file_path()
        else:
            if hasattr(image, 'read'):
                file = BytesIO(image.read())
            else:
                file = BytesIO(image['content'])

        im = Image.open(file)
        if im.format not in ('PNG', 'JPEG', 'JPG'):
            errors.append("Unsupported image type. Please upload only png or jpeg/jpg images")

        raise ValidationError(errors)

design_validator = ResolutionAndType(800,600)

from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

class Designs(models.Model):
    DesignState = models.TextChoices('DesignState', 'EN_PROCESO DISPONIBLE PENDIENTE ERROR_CONVERSION')    
    design_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    designer_name = models.CharField(max_length=200)
    designer_lastname = models.CharField(max_length=200)
    designer_email = models.EmailField(max_length=254)
    design_state = models.CharField(choices=DesignState.choices, max_length=20) 
    desing_original = models.ImageField(upload_to=path_original_image, validators=[design_validator]) 
    desing_converted = models.ImageField(upload_to=path_converted_image, blank=True)
    design_price = models.DecimalField(max_digits=100, decimal_places=0) 
    created_at = models.DateTimeField(editable=False)
    processing_start_date = models.DateTimeField(blank=True, null=True)
    processing_end_date = models.DateTimeField(blank=True, null=True)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created_at = timezone.now()
            self.design_state = self.DesignState.PENDIENTE        
        return super(Designs, self).save(*args, **kwargs)        

    class Meta:
        ordering = ['-id']

@receiver(post_delete, sender=Designs)
def designs_delete(sender, instance, **kwargs):
    # Cuando se este usando S3 bucket y no NFS, hay que pasar de .path a .name
    try:
        storage, path = instance.desing_original.storage, instance.desing_original.name
        storage.delete(path)
    except Exception as err:
        print(err)

    try:
        storage, path = instance.desing_converted.storage, instance.desing_converted.name
        storage.delete(path)
    except Exception as err:
        print(err)