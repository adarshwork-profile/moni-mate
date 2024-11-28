from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.safestring import mark_safe
import json
from collections import defaultdict
from django.utils.timezone import now
from django.contrib import messages



def reset_credit_limit(user): # function to reset credit_card billing cycle
    payment_methods = PaymentMethod.objects.filter(user=user,type='credit_card')
    today = now().date()

    if today.day == 1: # 1st day of month
        for method in payment_methods:
            if method.original_credit_limit is not None:
                method.credit_limit = method.original_credit_limit
                method.save()

@login_required
def dashboard(request):
    start_of_month = now().replace(day=1)
    # print(f'start of month {start_of_month}')
    expenses = Expense.objects.filter(user=request.user,date__gte=start_of_month).exclude(category='income').order_by('-date')
    payment_methods = PaymentMethod.objects.filter(user=request.user)


    # initializing warnings
    warnings = []

    # payment method balance warnings
    for method in payment_methods:
        if method.balance is not None and method.balance < method.minimum_balance:
            warnings.append(f'Balance for {method.name} is below minium required!')
        if method.type == 'credit_card' and method.credit_limit is not None:
            # calculating current spent ammount for credit card
            spend_amount = method.original_credit_limit - method.credit_limit
            if spend_amount >= method.spent_limit:
                warnings.append(f'Amount spend for {method.name} has reached/crossed the safe limit!')
    
    '''# NEEDS,WANTS ratio overflow warnings
    if MONTHLY_INCOME:
        need_amount , want_amount = MONTHLY_INCOME * ( NEEDS_PER / 100),MONTHLY_INCOME * ( WANTS_PER / 100)
    
        if NEEDS >= need_amount:
            warnings.append(f'Amount spend on "Needs" has reached or crossed the set limit!')
        elif WANTS >= want_amount:
            warnings.append(f'Amount spend on "Wants" has reached or crossed the set limit!')'''

    # reset credit limit if its start of a new month
    reset_credit_limit(request.user)

    # calculate category-wise totals
    category_totals = expenses.values('category').annotate(total=Sum('amount')).order_by('category')
    category_labels = [entry['category'].capitalize() for entry in category_totals]
    category_values = [float(entry['total']) for entry in category_totals]
    
    balances = {}

    for method in payment_methods: # update this logic in html for dashboard.
        if method.type == 'credit_card':
            balances[method.name] = method.credit_limit
        else:
            balances[method.name] = method.balance
    '''
    for expense in expenses:
        if expense.category:
            category_data[expense.category] += expense.amount'''
    context = {
        'balances': balances,
        'category_labels':json.dumps(category_labels),
        'category_values':json.dumps(category_values),
        'expenses':expenses,
        'payment_methods':payment_methods,
        'warnings':warnings,
    }
    # print(type(balances))
    # print(balances)
    return render(request, 'expense/dashboard.html',context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            '''global NEEDS,WANTS
            # accessing fields
            category = form.cleaned_data['category']
            amount = form.cleaned_data['amount']
            # processing data
            if category == 'needs':
                print('needs category detected')
                NEEDS += amount
            elif category == 'wants':
                WANTS += amount'''
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('expense:dashboard')
    else:
        form = ExpenseForm()
    return render(request,'expense/add_expense.html',{'form':form})

@login_required
def expense_history(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    return render(request, 'expense/expense_history.html',{'expenses':expenses})

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect('expense:dashboard')
    else:
        form = IncomeForm()
    return render(request,'expense/add_income.html',{'form':form})

@login_required
def payment_methods(request):
    payment_method = PaymentMethod.objects.filter(user=request.user)

    warnings = []

    # payment method balance warnings
    for method in payment_method:
        if method.balance is not None and method.balance < method.minimum_balance:
            warnings.append(f'Balance for {method.name} is below minium required!')
        if method.type == 'Credit Card' and method.credit_limit is not None:
            # calculating current spent ammount for credit card
            spend_amount = method.original_credit_limit - method.credit_limit
            if spend_amount >= method.spent_limit:
                warnings.append(f'Amount spend for {method.name} has reached/crossed the safe limit!')
    
    # handle form submission
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method_form = form.save(commit=False)
            payment_method_form.user = request.user
            payment_method_form.save()
            return redirect('expense:payment_methods')
    else:
        form = PaymentMethodForm()

    context = {
        'payment_methods':payment_method,
        'warnings':warnings,
        'form':form,
    }
    return render(request,'expense/payment_methods.html', context)

@login_required
def delete_payment_method(request,pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)

    if request.method == 'POST':
        payment_method.delete()
        messages.success(request, "Payment method deleted successfully.")
        return redirect('expense:payment_methods')
    return render(request, 'expense/confirm_delete.html', {'payment_method': payment_method})

# space for expense delete form
@login_required
def delete_expense(request,pk):
    expense = get_object_or_404(Expense,pk=pk,user=request.user)
    payment_method = expense.payment_method

    if request.method == 'POST':
        if payment_method.type == 'credit_card':
            payment_method.credit_limit += expense.amount
        else:
            payment_method.balance += expense.amount
        payment_method.save()
        expense.delete()
        return redirect('expense:expense_history')