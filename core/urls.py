from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "core"

urlpatterns = [
    # Auth
    path("",            views.index,   name="index"),
    path("login/",      auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/",     auth_views.LogoutView.as_view(),       name="logout"),
    path("register/",   views.register,                        name="register"),
    # Home / dashboard
    path("home/",       views.home,    name="home"),
    # Empresas / caminhões / inspeções  (já existiam)
    path("empresas/", views.company_list,   name="company_list"),
    path("empresa/nova/", views.company_create, name="company_create"),
    path("empresa/<int:company_id>/caminhoes/",
         views.truck_list,  name="truck_list"),
    path("empresa/<int:company_id>/caminhao/novo/",
         views.truck_create, name="truck_create"),
    path("caminhao/<int:truck_id>/inspecoes/",
         views.inspection_list, name="inspection_list"),
    path("caminhao/<int:truck_id>/inspecao/nova/",
         views.inspection_create, name="inspection_create"),
    path("inspecao/<int:inspection_id>/",
         views.inspection_detail, name="inspection_detail"),
    path("inspecao/<int:inspection_id>/editar/",
         views.inspection_edit, name="inspection_edit"),
     path("inspecao/<int:inspection_id>/delete/", views.inspection_delete, name="inspection_delete"),
     path("empresa/<int:company_id>/delete/", views.company_delete, name="company_delete"),
]
