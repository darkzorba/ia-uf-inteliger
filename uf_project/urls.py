from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
   openapi.Info(
      title="API de Gerenciamento de UFs",
      default_version='v1',
      description="API para gerenciar Unidades Federativas (UFs) do Brasil.",
      terms_of_service="https://www.google.com/policies/terms/", # Exemplo
      contact=openapi.Contact(email="contato@exemplo.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api_uf.urls')), # Incluindo as URLs da api_uf
    # URLs do Swagger / OpenAPI
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]