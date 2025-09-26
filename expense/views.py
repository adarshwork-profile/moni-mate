from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.safestring import mark_safe
import json, io, calendar
from collections import defaultdict
from django.utils.timezone import now
from django.contrib import messages
from assets.models import Asset, Liabilities
from datetime import datetime
from .support_func import generate_pdf
from django.http import HttpResponse
from core.models import UserProfile
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseForbidden

# SUPPORT FUNCTIONS ---
def hosting_alert():
    # Date as a string
    date_str = "2025-04-04" # update date here ( 2 days before actual date )
    given_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    if datetime.now().date() == given_date:
        send_mail(
            'Update Hosting Plan Date - MoniMate (Admin)',
            'Dear Admin\n,Please update the hosting plan date by visiting "pythonanywhere" website. Also update the next reminder date in the "expense>views.py(file)>hosting_alert(function)".\nRegards,\nMoniMate Team',
            settings.DEFAULT_FROM_EMAIL,
            ['freelance.blackfly123@gmail.com'],
            fail_silently = True,
        )

def reset_credit_limit(user): # function to reset credit_card billing cycle
    payment_methods = PaymentMethod.objects.filter(user=user,type='credit_card')
    today = now().date()

    if today.day == 1: # 1st day of month
        for method in payment_methods:
            if method.original_credit_limit is not None:
                method.credit_limit = method.original_credit_limit
                method.save()
# calculate asset-liability ratio
def networth_ratio(request):
    assets = Asset.objects.filter(user = request.user)
    liabilities = Liabilities.objects.filter(user = request.user)
    networth_value = [float(sum(asset.current_value for asset in assets)),float(sum(lib.total_amount for lib in liabilities ))]
    networth_labels = ['Assets','Liabilites']
    return networth_labels,networth_value

def billing_due(date):
    if date == datetime.now().day:
        return True
    else:
        return False

def monthly_report(request,month,year):
    expenses = Expense.objects.filter(user = request.user,date__month = month,date__year = year).order_by('date')
    row_data = []
    needs,wants,savings,total_spending = 0,0,0,0
    if expenses:
        for expense in expenses:
            row_data.append({'name':expense.name,'category':expense.get_category_display(),'amount':str(expense.amount),'date':str(expense.date),'payment_method':expense.payment_method.name,'transaction_mode':expense.get_transaction_mode_display()})

            if expense.category != 'income':
                total_spending += expense.amount
            # categorizing expense
            if expense.category == 'needs':
                needs += expense.amount
            elif expense.category == 'wants':
                wants += expense.amount
            elif expense.category == 'savings':
                savings += expense.amount
        # ratio calculation
        if total_spending > 0:
            if needs > 0:
                need_rat = round((needs/total_spending)*100,2)
            else:
                need_rat = 0
            if wants > 0:
                want_rat = round((wants/total_spending)*100,2)
            else:
                want_rat = 0
            if savings > 0:
                saving_rat = round((savings/total_spending)*100,2)
            else:
                saving_rat = 0
        summary = {
            'Total Needs':f'{needs} ({need_rat}%)',
            'Total Wants':f'{wants} ({want_rat}%)',
            'Total Savings':f'{savings} ({saving_rat}%)',
            'Total Spending':total_spending
        }
        return row_data,summary
    else:
        return None,None

#-----------------------

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
        if method.type == 'cash':
            if method.balance < 100:
                warnings.append('Your wallet is low on cash, withdraw cash from nearby ATM.')
            continue
        if method.type == 'credit_card' and billing_due(method.billing_date):
            warnings.append(f'Reminder: Today is the billing day for your credit card - {method.name}')
        if method.type == 'credit_card' and method.credit_limit is not None:
            # calculating current spent ammount for credit card
            spend_amount = method.original_credit_limit - method.credit_limit
            if spend_amount >= method.spent_limit:
                warnings.append(f'Amount spend for {method.name} has reached/crossed the safe limit!')
        if method.balance is not None:
            if method.balance < method.minimum_balance:
                warnings.append(f'Balance for {method.name} is below minimum required!')


    # reset credit limit if its start of a new month
    reset_credit_limit(request.user)
    # total expenses ( current month)
    total_expense = expenses.aggregate(overall_total=Sum('amount'))['overall_total']
    # calculate category-wise totals
    category_totals = expenses.values('category').annotate(total=Sum('amount')).order_by('category')
    category_labels = [entry['category'].capitalize() for entry in category_totals]
    category_values = [float(entry['total']) for entry in category_totals]

    balances = {}

    for method in payment_methods: # Display account balances
        if method.type == 'credit_card':
            balances[method.name] = method.credit_limit
        else:
            balances[method.name] = method.balance

    # networth ratio
    networth_labels,networth_values = networth_ratio(request)
    print(networth_values,networth_labels)
    context = {
        'balances': balances,
        'category_labels':json.dumps(category_labels),
        'category_values':json.dumps(category_values) if category_values else None,
        'total_expense':total_expense if total_expense else 0,
        'payment_methods':payment_methods,
        'warnings':warnings,
        'networth_labels':networth_labels,
        'networth_values':networth_values if networth_values else None,
    }
    # print(type(balances))
    return render(request, 'expense/dashboard.html',context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('expense:dashboard')
    else:
        form = ExpenseForm(user=request.user)
    return render(request,'expense/add_expense.html',{'form':form})

@login_required
def expense_history(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    return render(request, 'expense/expense_history.html',{'expenses':expenses})

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST, user=request.user)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect('expense:dashboard')
    else:
        form = IncomeForm(user=request.user)
    return render(request,'expense/add_income.html',{'form':form})

@login_required
def payment_methods(request):
    payment_method = PaymentMethod.objects.filter(user=request.user)

    warnings = []

    # payment method balance warnings
    for method in payment_method:
        if method.type == 'cash':
            if method.balance < 100:
                warnings.append('Your wallet is low on cash, withdraw cash from nearby ATM.')
            continue
        if method.type == 'credit_card' and billing_due(method.billing_date):
            warnings.append(f'Reminder: Today is the billing day for your credit card - {method.name}')
        if method.type == 'credit_card' and method.credit_limit is not None:
            # calculating current spent ammount for credit card
            spend_amount = method.original_credit_limit - method.credit_limit
            if spend_amount >= method.spent_limit:
                warnings.append(f'Amount spend for {method.name} has reached/crossed the safe limit!')
        if method.balance is not None:
            if method.balance < method.minimum_balance:
                warnings.append(f'Balance for {method.name} is below minimum required!')

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

# Edit payment method function here (balance edit) 
@login_required
def edit_payment_method(request,pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)

    # add request post for modifying after editing, and in else clause the code for displaying the edit form page. 
    # ( edit form contains option to either update in history or silent edit )
    
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
    category = expense.category

    if request.method == 'POST':
        if category == 'income':
            payment_method.balance -= expense.amount
        else:
            if payment_method.type == 'credit_card':
                payment_method.credit_limit += expense.amount
            else:
                payment_method.balance += expense.amount
        payment_method.save()
        expense.delete()
        return redirect('expense:expense_history')

# settings
@login_required
def settings(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'inflation-form':
            profile = UserProfile.objects.get(user = request.user)
            profile.inflation = int(request.POST.get('new-value'))
            profile.save()
            return redirect('expense:settings')
        elif form_type == 'expense-report':
            # data generation
            report_type = str(request.POST.get('report-type'))
            year = int(request.POST.get('year'))
            if report_type == 'monthly':
                month = str(request.POST.get('month'))
                month_no = list(calendar.month_name).index(month)
                row_data,summary = monthly_report(request,month_no,year)
                if not row_data or not summary:
                    return HttpResponseForbidden("No expense data for the selected time frame.")
                # preparing data
                data = {
                    month:row_data,
                    'summary':summary
                }
                # generate pdf
                pdf_buffer = generate_pdf(data,request.user.username,report_type,month)
            elif report_type == 'yearly':
                data = {}
                for month in range(1,13):
                    row_data,summary = monthly_report(request,month,year)
                    if row_data and summary:
                        data[calendar.month_name[month]] = [row_data,summary]
                if len(data.keys()) <= 0:
                    return HttpResponseForbidden("No expense data for the selected time frame.")
                # generate pdf
                pdf_buffer = generate_pdf(data,request.user.username,report_type)
            # server pdf
            response = HttpResponse(pdf_buffer, content_type= 'application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Expense_Report_{report_type}.pdf"'
            return response
    profile = UserProfile.objects.get(user=request.user)
    context = {
        'username':profile.user.username,
        'email':profile.notify_email,
        'inflation':profile.inflation,
    }
    return render(request,'expense/settings.html',context)

