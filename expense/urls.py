from django.urls import path
from . import views


app_name = 'expense'

urlpatterns = [
    path('',views.dashboard,name='dashboard'),
    path('expense/',views.add_expense,name='add_expense'),
    path('history/',views.expense_history,name='expense_history'),
    path('income/',views.add_income,name='add_income'),
    path('payments/',views.payment_methods,name='payment_methods'),
    path('payments/delete/<int:pk>/',views.delete_payment_method,name='delete_payment_method'),
    path('expense/delete/<int:pk>/',views.delete_expense,name='delete_expense'),
]
