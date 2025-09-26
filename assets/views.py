from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Asset,Liabilities, GrowthHistory
from .forms import AssetForm,LiabilityForm
from . import support_func
from core.models import UserProfile
from datetime import datetime
from django.db.models import Sum
from django.http import HttpResponseForbidden
from decimal import Decimal


# support functions
# deviations calculator
def dev_msg():
    nifty,mrkt_val,mrkt_sntim = support_func.deviator()
    analysis = {'nifty':nifty,'market_val':mrkt_val,'market_sentim':mrkt_sntim}
    # conclusion
    #print(mrkt_sntim,mrkt_val)
    if mrkt_val < 0 and mrkt_sntim < 0:
        # extreme low
        if mrkt_val < -11 and mrkt_sntim < -19:
            analysis['msg_head'] = 'Deeply Undervalued'
            analysis['msg_body'] = 'Aggressive SIP & lump-sum investments suggested.'
        else:
            analysis['msg_head'] = 'Undervalued'
            analysis['msg_body'] = 'Adequate SIP & lump-sum investments are suggested.'
    elif mrkt_val < 0 and mrkt_sntim > 0:
        analysis['msg_head'] = 'Market: Inexpensive | Sentiments: Greedy'
        analysis['msg_body'] = 'Cautious SIP investments only. Parking in liquid funds are suggested.'
    elif mrkt_val > 0 and mrkt_sntim < 0:
        analysis['msg_head'] = 'Market: Expensive | Sentiments: Fearful'
        analysis['msg_body'] = 'Moderate SIP investments only. Hybrid funds are suggested.'
    elif mrkt_val > 0 and mrkt_sntim > 0:
        # extreme high
        if mrkt_val > 11 and mrkt_sntim > 24:
            analysis['msg_head'] = 'Bubble Risk'
            analysis['msg_body'] = 'Reduce exposure, avoid new investments in equity funds.'
        else:
            analysis['msg_head'] = 'Overvalued'
            analysis['msg_body'] = 'Avoiding lump-sum and focusing on small SIPs suggested.'
    elif mrkt_val ==  0 and mrkt_sntim == 0:
        analysis['msg_head'] = 'Fair Value'
        analysis['msg_body'] = 'Balanced SIPs and small lump-sum investments suggested.'
    elif mrkt_val ==  0 and mrkt_sntim > 0:
        analysis['msg_head'] = 'Market: Fair | Sentiments: Greedy'
        analysis['msg_body'] = 'Moderate SIPs and avoiding lump-sum investments suggested.'
    elif mrkt_val ==  0 and mrkt_sntim < 0:
        analysis['msg_head'] = 'Market: Fair | Sentiments: Fearful'
        analysis['msg_body'] = 'Balanced SIP and lump-sum investments suggested.'
    elif mrkt_val >  0 and mrkt_sntim == 0:
        analysis['msg_head'] = 'Market: Expensive | Sentiments: Fair'
        analysis['msg_body'] = 'Focus on small SIPs and consider partial profit booking.'
    elif mrkt_val <  0 and mrkt_sntim == 0:
        analysis['msg_head'] = 'Market: Inexpensive | Sentiments: Fair'
        analysis['msg_body'] = 'Moderate SIPs and lump-sum investments suggested.'
    return analysis

# projected growth amount
def growth_prjct(assets):
    lin_total_crnt,lin_grwth,cmpd_total_crnt,cmpd_grwth = 0,0,0,0
    linears = ['debt_mf','fixed_deposit','others']
    for asset in assets:
        if asset.type in linears:
            lin_total_crnt += asset.current_value
            lin_grwth += asset.current_value * Decimal(asset.growth_rate)
        else:
            cmpd_total_crnt += asset.current_value
            cmpd_grwth += asset.current_value * Decimal(asset.growth_rate)
    # linear ogr (overall growth rate)
    try:
        lin_ogr = lin_grwth/ lin_total_crnt
    except ZeroDivisionError:
        lin_ogr = 0
    # compound ogr (overall growth rate)
    try:
        cmpd_ogr = cmpd_grwth / cmpd_total_crnt
    except ZeroDivisionError:
        cmpd_ogr = 0
    # calculate year-wise projected amount (linear & compound)
    grwth_prjctns = []
    for years in range(11):
        lin_prjct = lin_total_crnt * ( 1 + lin_ogr * years )
        if cmpd_ogr > 0:
            cmpd_prjct = cmpd_total_crnt * (1 + cmpd_ogr)**years
        else:
            #print(cmpd_ogr)
            cmpd_prjct = cmpd_total_crnt * (1 + cmpd_ogr * years) # linear projection for negative growth %
        grwth_prjctns.append(round(float(lin_prjct + cmpd_prjct),2))
        print(f'Linear growth for year {years}: {round(float(lin_prjct),2)}\nCompund growth for year {years}:{round(float( cmpd_prjct) ,2)}')
    return grwth_prjctns

# individual growth rate calculation
def cl_grwth(asset,current_value,linear=False):
    try:
        monthly_grwth =  (current_value - asset.current_value)/asset.current_value
        if linear:# linear growth rate
            yearly_grwth =  (monthly_grwth * 12) * 100
        else: # compound growth rate
            yearly_grwth = ((1 + monthly_grwth)**12 -1) * 100
        
        # checking for previous growth history
        gr_hist = GrowthHistory.objects.filter(asset = asset)
        if gr_hist and gr_hist.count() > 1:
            print('growth history is more than 1 ')
            historical_growth = sum(hist.growth_rate for hist in gr_hist)
            growth_num = gr_hist.count()
            yearly_grwth = (historical_growth + float(yearly_grwth)) /(growth_num + 1) # average of previous and now value
            # check if it contains historical data which is older than 1 year
            for hist in gr_hist:
                if hist.added_on.year <= datetime.now().year - 1 and hist.added_on.month <= datetime.now().month:
                    hist.delete()
        # return yearly growth rate
        return yearly_grwth
        
    except ZeroDivisionError:
        return 0

# asset update alerts
def update_alert():
    if datetime.now().day == 28:
        return True
    else:
        return False
# -----------------------------------------------

@login_required
def balance_sheet(request):
    assets = Asset.objects.filter(user=request.user)
    profile = UserProfile.objects.filter(user = request.user)
    liabilities = Liabilities.objects.filter(user=request.user)
    # obtain inflation data
    for data in profile:
        infltn = data.inflation
    # calculate overall growth %
    total_invst_val,total_grwth_val = 0,0
    for asset in assets:
        total_invst_val += asset.invested_value
        total_grwth_val += (asset.invested_value * Decimal(asset.growth_rate))
    try:
        overall_growth = float(total_grwth_val/total_invst_val)
    except ZeroDivisionError:
        overall_growth = 0
    # growth projections
    grwth_prjctn = growth_prjct(assets)
    this_year = int(datetime.now().year)
    grwth_label = [x for x in range(this_year,this_year + 11)]

    real_grwth = ((1 + (overall_growth/100)) / (1 + (infltn/100)) - 1) # inflation adjusted growth
    # banner logic
    analysis = dev_msg()
    # type-wise asset data
    type_totals = assets.values('type').annotate(total=Sum('current_value')).order_by('type')
    type_label = [Asset(type = entry['type']).get_type_display() for entry in type_totals]
    type_value = [float(entry['total']) for entry in type_totals]
    context = {
        'assets': assets,
        'overall_growth':round(overall_growth,2),
        'analysis':analysis,
        'growth_projection':grwth_prjctn[-1],
        'growth_labels':grwth_label,
        'growth_projections':grwth_prjctn,
        'inflation':infltn,
        'real_growth':round(real_grwth,2),
        'type_labels':type_label,
        'type_values':type_value if type_value else None,
        'update_alert':update_alert(),
        'liabilities':liabilities,
    }
    return render( request, 'assets/balance_sheet.html',context)

@login_required
def add_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.user = request.user
            asset.current_value = asset.invested_value
            asset.save()
            return redirect ('assets:wealth')
    else:
        form = AssetForm()
        return render(request, 'assets/add_assets.html', {'form':form})

@login_required
def asset_view(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)

    if request.method == 'POST':
        update_type = request.POST.get('update-type')
        update_value = Decimal(request.POST.get('new-value'))

        if str(update_type) == 'invested':
            try:
                value_diff = update_value - asset.invested_value
                asset.invested_value = update_value
                asset.current_value = asset.current_value + value_diff
                asset.save()
                return redirect('assets:asset-view', asset_id=asset.id)  # Redirect to the same page or another
            except ValueError:
                return HttpResponseForbidden("Invalid input. Please provide numeric values.")
        elif str(update_type) == 'current':
            linears = ['debt_mf','fixed_deposit','others']
            try:
                if asset.type in linears:
                    asset.growth_rate = round(cl_grwth(asset,update_value,True),2)
                else:
                    asset.growth_rate = round(cl_grwth(asset,update_value),2)               
                asset.current_value = update_value
                asset.save()
                # update growth rate into growth history
                GrowthHistory.objects.create(asset = asset,invested_value = asset.invested_value,current_value = update_value,growth_rate = asset.growth_rate)
                print('growth history updated ( new object created)')
                return redirect('assets:asset-view', asset_id=asset.id)  # Redirect to the same page or another
            except ValueError:
                return HttpResponseForbidden("Invalid input. Please provide numeric values.")
        else:
            return HttpResponseForbidden("All fields are required.")

    return render(request, 'assets/assets_view.html', {'asset': asset})

@login_required
def delete_asset(request,pk):
    asset = get_object_or_404(Asset,pk=pk,user=request.user)
    if request.method == 'POST':
        asset.delete()
        return redirect('assets:wealth')
    return render(request, 'assets/delete_asset.html',{'asset':asset})

@login_required
def add_liability(request):
    if request.method == 'POST':
        form = LiabilityForm(request.POST)
        if form.is_valid():
            lib = form.save(commit=False)
            lib.user = request.user
            lib.save()
            return redirect ('assets:wealth')
    else:
        form = LiabilityForm()
        return render(request, 'assets/add_liability.html', {'form':form})

@login_required
def liability_view(request, lib_id):
    lib = get_object_or_404(Liabilities, id=lib_id)

    if request.method == 'POST':
        update_type = request.POST.get('update-type')
        update_value = request.POST.get('new-value')

        if str(update_type) == 'emi':
            try:
                lib.installments = Decimal(update_value)
                lib.save()
                return redirect('assets:lib-view', lib_id=lib.id)  # Redirect to the same page or another
            except ValueError:
                return HttpResponseForbidden("Invalid input. Please provide numeric values.")
        elif str(update_type) == 'total':
            try:
                lib.total_amount = Decimal(update_value)
                lib.save()
                return redirect('assets:lib-view', lib_id=lib.id)  # Redirect to the same page or another
            except ValueError:
                return HttpResponseForbidden("Invalid input. Please provide numeric values.")
        elif str(update_type) == 'notes':
            try:
                lib.notes = str(update_value)
                lib.save()
                return redirect('assets:lib-view', lib_id=lib.id)  # Redirect to the same page or another
            except ValueError:
                return HttpResponseForbidden("Invalid input. Please provide string values.")
        else:
            return HttpResponseForbidden("All fields are required.")

    return render(request, 'assets/liability_view.html', {'liability': lib})

@login_required
def delete_lib(request,pk):
    lib = get_object_or_404(Liabilities,pk=pk,user=request.user)
    if request.method == 'POST':
        lib.delete()
        return redirect('assets:wealth')
    return render(request, 'assets/delete_liability.html',{'liability':lib})






