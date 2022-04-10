from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .models import Product, Budget
from .forms import ProductForm, BudgetForm
import datetime
import pandas as pd


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'list/login.html', {
                    'message': 'Invalid credentials, please try again.'
            })
    else:
        return render(request, 'list/login.html')


def logout_view(request):
    logout(request)
    return render(request, 'list/login.html')


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        date_now = datetime.date.today().strftime("%Y-%m-%d")
        date_input = request.POST.get('input_date')
        if date_now != date_input and date_input != None:
            date_now = date_input
       
        products = Product.objects.filter(buyDate=f"{date_now}")
        total_price = 0
        for product in products:
            total_price += product.total()

        return render(request, 'list/index.html', {
            'date': date_now,
            'products': products,
            'total_price': total_price
        })


def delete(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        product = Product.objects.get(pk=product_id)
        if request.method == 'POST':
            budget = product.budget
            product.delete()
            if budget != None:
                budget.value += product.price * product.quantity
                budget.save()
            return redirect('index')
        return render(request, "list/delete.html", {'product': product})


def add(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        if request.method == 'GET':
            form = ProductForm()
            return render(request, "list/add.html", {'form': form})
        else:
            form = ProductForm(request.POST)
            if form.is_valid():
                form.save()
                budget = form.cleaned_data.get('budget')
                if budget != None:
                    budget.value -= form.cleaned_data.get('price') * form.cleaned_data.get('quantity') 
                    budget.save()
            return redirect('index')


def edit(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        if request.method == 'GET':
            product = Product.objects.get(pk=product_id)
            form = ProductForm(instance=product)
            return render(request, 'list/edit.html', {'form': form, 'product': product})
        else:
            product = Product.objects.get(pk=product_id)
            stPrice = product.price
            stQuantity = product.quantity
            stBudget = product.budget
            form = ProductForm(request.POST, instance=product)
            if form.is_valid():
                form.save()
                ndBudget = form.cleaned_data.get('budget')
                ndPrice = form.cleaned_data.get('price')
                ndQuantity = form.cleaned_data.get('quantity')
                if ndBudget == stBudget:
                    ndBudget.value -= ndPrice * ndQuantity - stPrice * stQuantity
                    ndBudget.save()
                elif ((stBudget == None) and (ndBudget != None)):
                    ndBudget.value -= ndPrice * ndQuantity
                    ndBudget.save()
                elif ((stBudget != None) and (ndBudget == None)):
                    stBudget.value += ndPrice * ndQuantity
                    stBudget.save()
                elif ndBudget != stBudget:
                    ndBudget.value -= ndPrice * ndQuantity
                    ndBudget.save()
                    stBudget.value += stPrice * stQuantity
                    stBudget.save()
            return redirect('index')


def stats(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        try:
            first_product = Product.objects.all().order_by('buyDate')[0]
            last_product = Product.objects.all().order_by('-buyDate')[0]
            first_product_date = first_product.buyDate.strftime('%Y-%m-%d')
            last_product_date = last_product.buyDate.strftime('%Y-%m-%d')

            products = Product.objects.filter(buyDate__range=[first_product_date, last_product_date])
            labels_of_date = list(set([label.buyDate.strftime('%Y-%m-%d') for label in products]))
            labels_of_date.sort()

            total_price = 0
            for product in products:
                total_price += product.total()


            if request.method == 'POST':
                first_date = request.POST.get('first_date')
                last_date = request.POST.get('last_date')
                if first_date <= last_date:
                    first_product_date = first_date
                    last_product_date = last_date
                else:
                    return render(request, 'list/stats.html', {
                        'message': 'Invalid dates, please try again.'
                    })

            
            first = pd.to_datetime(first_product_date, format="%Y-%m-%d")
            last = pd.to_datetime(last_product_date, format="%Y-%m-%d")
            days_range = last - first


            # Highest expense function
            def highest_expense():
                prods = Product.objects.filter(buyDate__range=[first_product_date, last_product_date])
                prod = [dict(id = p.id, total = float(p.total())) for p in prods]
                prod = sorted(prod, key=lambda x: x['total'], reverse=True)
                prod = prods.get(id = prod[0]['id'])
                return f"{prod.quantity}x {prod.name.upper()} for {prod.total()}€ on {prod.buyDate}"


            # Highest expense witout a budget function
            def highest_expense_none(): 
                prods = Product.objects.filter(buyDate__range=[first_product_date, last_product_date]).filter(budget=None)
                if len(prods) != 0:
                    prod_none = sorted(prods, key= lambda x: x.total())[-1]
                    return f"{prod_none.quantity}x {prod_none.name.upper()} for {prod_none.total()}€ on {prod_none.buyDate}"
                else:
                    return f"No expenses without a budget yet"


            # Highest expenses by budgets function
            def highest_expense_budget():
                pros = Product.objects.filter(buyDate__range=[first_product_date, last_product_date])
                budgets_ids = [b.budget.id for b in pros if b.budget != None]
                budgets_set = set(budgets_ids)
                prod_list= []
                for budget_id in budgets_set:
                    element = Product.objects.filter(budget__id=budget_id).order_by('price')[0]
                    prod_list.append(f"{element.budget}: {element.quantity}x {element.name.upper()} for {element.total()}€ on {element.buyDate}")
                if len(prod_list) == 0:
                    prod_list.append("No expenses with a budget yet")
                return prod_list

            # Chart data functions
            data_list = []
            budget_element = set([p.budget for p in products])
            def chart_data():
                chart_element = {'label': '', 'backgroundColor': '', 'data': []}
                chart_elements_list = []
                for idx, budg in enumerate(budget_element):
                    chart_element['label'] = str(budg)
                    if str(budg) == 'None':
                        chart_element['backgroundColor'] = 'rgba(128, 128, 128, 0.5)'
                    else:    
                        chart_element['backgroundColor'] = Budget.objects.get(name=str(budg)).color()
                    chart_element['data'] = data_list[idx]
                    chart_elements_list.append(chart_element)
                    chart_element = {'label': '', 'backgroundColor': '', 'data': []}
                return chart_elements_list
            

            # Data for data_list variable above
            for b in budget_element:
                elements_list = []
                for d in labels_of_date:
                    if products.filter(budget=b).filter(buyDate=d):
                        prs = products.filter(budget=b).filter(buyDate=d)
                        summ = 0
                        for i in prs:
                            summ += i.total()        
                        elements_list.append(float(summ))
                    else:
                        elements_list.append(0)
                data_list.append(elements_list)
            

            return render(request, "list/stats.html", {
                'total_price': total_price,
                'labels': labels_of_date,
                'first': first_product_date,
                'last': last_product_date,
                'days_range': days_range.days + 1,
                'daysWith': len(labels_of_date),
                'highest_expense': highest_expense(),
                'chart_data': chart_data(),
                'prod_list': highest_expense_budget(),
                'highest_prod_none': highest_expense_none()
                
                })
        except:
            return render(request, 'list/stats.html', {
                'message': 'No data, please add at least one expense in LISTS.'})      
     

def budget(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        budgets = Budget.objects.all()
        return render(request, 'list/budget.html', {
            'budgets': budgets
        })


def deleteBudget(request, budget_id):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        budget = Budget.objects.get(pk=budget_id)
        if request.method == 'POST':
            budget.delete()
            return redirect('budget')
        return render(request, "list/deleteBudget.html", {'budget': budget})


def addBudget(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        if request.method == 'GET':
            form = BudgetForm()
            return render(request, "list/addBudget.html", {'form': form})
        else:
            form = BudgetForm(request.POST)
            if form.is_valid():
                form.save()
            return redirect('budget')


def editBudget(request, budget_id):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        if request.method == 'GET':
            budget = Budget.objects.get(pk=budget_id)
            form = BudgetForm(instance=budget)
            return render(request, 'list/editBudget.html', {'form': form, 'budget': budget})
        else:
            budget = Budget.objects.get(pk=budget_id)
            form = BudgetForm(request.POST, instance=budget)
            if form.is_valid():
                form.save()
            return redirect('budget')


def infoBudget(request, budget_id):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        budget = Budget.objects.get(pk=budget_id)
        products = reversed([f"{i.quantity}x {i.name.upper()} for {i.total()}€ on {i.buyDate}" for i in budget.products.all()])
        
        total = 0
        for i in budget.products.all():
            total =+ i.total()

        return render(request, 'list/infoBudget.html', {
            'products': products,
            'budget': budget,
            'total': total
        })

def infoNoneBudget(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        prods = Product.objects.filter(budget=None)
        products = reversed([f"{i.quantity}x {i.name.upper()} for {i.total()}€ on {i.buyDate}" for i in prods])
        
        total = 0
        for i in prods:
            total =+ i.total()

        return render(request, 'list/infoNoneBudget.html', {
            'products': products,
            'total': total
        })

