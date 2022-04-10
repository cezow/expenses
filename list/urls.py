from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('delete/<str:product_id>', views.delete, name='delete'),
    path('add', views.add, name='add'),
    path('edit/<str:product_id>', views.edit, name='edit'),
    path('budget', views.budget, name='budget'),
    path('add_budget', views.addBudget, name='addBudget'),
    path('edit_budget/<str:budget_id>', views.editBudget, name='editBudget'),
    path('delete_budget/<str:budget_id>', views.deleteBudget, name='deleteBudget'),
    path('budget_info/<str:budget_id>', views.infoBudget, name='infoBudget'),
    path('budget_info_none', views.infoNoneBudget, name='infoNoneBudget'),
    path('stats', views.stats, name='stats')
]