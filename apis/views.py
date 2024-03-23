from email.utils import parsedate_to_datetime
import genericpath
from pyexpat.errors import messages
import random
from types import GenericAlias
from django.http import HttpResponse
from django.shortcuts import render, redirect
from grpc import GenericRpcHandler
from numpy import generic
from .models import Expense, UserStatus,Email,MailExpense,User
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from openai import ChatCompletion
import requests
from django.urls import reverse
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import imaplib
import email
import re
import google.generativeai as genai
from datetime import datetime, timedelta
import json
from rest_framework import generics
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from .models import User
from django.shortcuts import render
from .serializers import MailExpenseSerializer, UserSerializer,User
from django.http import JsonResponse
# from .utils import generate_jwt_token
import jwt
from .models import User
from .forms import LoginForm, UserForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate , login
from django.http import HttpResponse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from .forms import UserForm
from django.shortcuts import render, redirect
from django.contrib import messages

# from rest_framework import status
# from rest_framework.generics import CreateAPIView, RetrieveAPIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
# from .serializers import UserRegistrationSerializer
# from .serializers import UserLoginSerializer, UserDetailSerializer
# from .models import UserProfile

 # Updated import
# from .tasks import process_emails

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from datetime import datetime
import json
from collections import defaultdict
from .utils import compare_p
# Create your views here.
conversation=""
info_string=""
# home
def prompt(request):
    cookies = request.COOKIES
    expenses = Expense.objects.all()
    my_expense=format_expenses_as_table(expenses)
    user_status = UserStatus.objects.filter(user_id=cookies["id"]).first()
    my_status=format_user_status_table(user_status)
    
    request.session['conversation']=[]
    request.session['conversation'].append({"role": "system", "content": "Hello, you are a financial bot your name is DE Shaw Bot. I am sharing you my expenditure data in the format Item |Amount|Category|Date and the amount are in Indian National Rupees and always try to retun the responses with data "+my_expense+"\nNow I am giving you my user status too to help you make more personalised responses and advices (the user status is in format attribute|value):"+my_status})

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
class MailExpenseListCreateView(generics.ListCreateAPIView):
    queryset = MailExpense.objects.all()
    serializer_class = MailExpenseSerializer

class MailExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MailExpense.objects.all()
    serializer_class = MailExpenseSerializer


def get_user_credentials(request, user_id):
    try:
        email, app_password = User.get_user_credentials(user_id)
        if email and app_password:
            return JsonResponse({'email': email, 'app_password': app_password})
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def mail_expenses_page(request):
    # process_emails

    cookies = request.COOKIES
    try:
        user_id = cookies["id"]
    except:
        redirect("login")
    user = User.objects.filter(user_id=user_id).first()
    print(cookies)
    process_emails(user.gmail,user.app_password,user.pk)
    
    return redirect(to="/")
  
    

# def generate_token(request, user_id):
#     try:
#         user = User.objects.get(user_id=user_id)
#         token = generate_jwt_token(user)
#         return JsonResponse({'token': token})
#     except User.DoesNotExist:
#         return JsonResponse({'error': 'User does not exist'}, status=404)

# def decode_token(request):
#     token = request.GET.get('token')
#     if token:
#         try:
#             decoded_message = jwt.decode(token)
#             return JsonResponse(decoded_message)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)
#     else:
#         return JsonResponse({'error': 'Token not provided'}, status=400)


def home(request):
    print(request.session)
    # conversation= request.session['conversation']
    conversation= ""
    cookies = request.COOKIES
    try:
        user_id = cookies["id"]
    except:
        redirect("login")
    user = User.objects.filter(user_id=user_id).first()
    expenses = Expense.objects.all()

    
    if request.method == 'POST':
        print(request.COOKIES)
        # month = request.POST['month']
        # year = request.POST['year']
        # expenses = Expense.objects.filter(date__year=year, date__month=month)
    expenses = Expense.objects.all()
    return render(request, 'index.html', {'expenses': expenses, 'conversation': conversation})

# create
@csrf_exempt
def add(request):
    cookies = request.COOKIES
    try:
        user_id = cookies["id"]
    except:
        redirect("login")
    print(user_id)
    user = User.objects.filter(user_id=user_id)
    if user.exists():
        user=user.first()
    else:
        print("I dont exist")
        redirect("login")

    if request.method == 'POST':
        
        item = request.POST['item']
        amount = int(request.POST['amount'])
        category = request.POST['category']
        date = request.POST['date']

        expense = Expense(user=user,item=item, amount=amount, category=category, date=date)
        expense.save()
        # prompt(request)
        # # Update total_expenses for the user
        user_status = UserStatus.objects.get(user_id=user_id)
        user_status.total_expenses += amount
        user_status.save()

    return redirect(home)

def add_user_status(request):
    cookies = request.COOKIES
    try:
        user_id = cookies["id"]
    except:
        redirect("login")
    user = User.objects.filter(pk=user_id).first()

    if request.method == "POST":
        allowedexpense = int(request.POST.get("allowedexpense"))
        monthlybudget = int(request.POST.get("monthlybudget"))
        pincode = int(request.POST.get("pincode"))
        # gmail=str(request.POST.get("gmail"))
        # app_password=str(request.POST.get("a"))
        # Create or update UserStatus for the user
        user_status = UserStatus.objects.filter(user=user)
        if user_status.exists():
            user_status = user_status.first()
            # user_status=user
            user_status.allowedexpense = allowedexpense
            user_status.monthlybudget = monthlybudget
            user_status.pincode = pincode
            # user_status.gmail = gmail
            # user_status.app_password = app_password 
        else:
         user_status= UserStatus.objects.create(allowedexpense=allowedexpense,monthlybudget=monthlybudget,pincode=pincode,user=user)
        print(user_status)
        
        user_status.save()
        prompt(request)
    return redirect(expense_summary)  # Render the form to add user status

def update(request,id=None):
    cookies = request.COOKIES
    try:
        user_id = cookies["id"]
    except:
        redirect("login")
    user = User.objects.filter(user_id=user_id).first()
    user_id = user_id
    expense_fetched = Expense.objects.filter(pk=id).first()

    user_status = UserStatus.objects.filter(user_id=user_id).first()  # Assuming user_id 1 is the only user
    user_status.total_expenses -= expense_fetched.amount
    
    if request.method == 'POST':
        
        item = request.POST['item']
        amount = int(request.POST['amount'])
        category = request.POST['category']
        date = request.POST['date']
        if expense_fetched:
            # expense_fetched=expense_fetched.first()
            expense_fetched.user=user
            expense_fetched.item = item
            expense_fetched.amount = amount
            expense_fetched.category = category
            expense_fetched.date = date
            user_status.total_expenses+=amount
            user_status.save()
            expense_fetched.save()
            prompt(request)
    return redirect(home)

def delete(request,id=None):
    cookies = request.COOKIES
    try:
        user_id = cookies["id"]
    except:
        redirect("login")
    user = User.objects.filter(user_id=user_id).first()
    user_id = user_id
    expense_fetched = Expense.objects.filter(pk=id)
    if expense_fetched.exists():
        expense_fetched=expense_fetched.first()
        user_status = UserStatus.objects.get(user_id=user_id)  # Assuming user_id 1 is the only user
        user_status.total_expenses -= expense_fetched.amount
        user_status.save()
    
        expense_fetched.delete()
    prompt(request)
    return redirect(home)

# @api_view(["POST"])
def expense_summary(request):
    # data = request.data
    cookies = request.COOKIES
    user_id=cookies["id"]
    # cookies = request.COOKIES
    # try:
    #     user_id = cookies["id"]
    # except:
    #     redirect("login")

    expenses = Expense.objects.filter(user=user_id)
    print(expenses)

    # Calculate total spending for each category
    category_totals = expenses.values('category').annotate(total=Sum('amount'))
    print(expense_summary)
    # Calculate total spending across all categories
    total_spending = expenses.aggregate(total=Sum('amount'))['total']

    # Calculate percentage spending for each category
    category_percentages = {}
    for category_total in category_totals:
        print("iwork")
        category_percentages[category_total['category']] = (category_total['total'] / total_spending) * 100
    
    # Aggregate spending data based on dates
    print(user_id,"q")
    daily_spending_data = expenses.values('date').annotate(total=Sum('amount'))
    print(user_id,"q2")
    user_status = UserStatus.objects.filter(user=user_id).first()
    print()
    total =0
    for data in list(daily_spending_data):
        total+=int(data["total"])
    print(total)
    context = {
        'category_percentages': category_percentages,
        'daily_spending_data': daily_spending_data,
        'user_status': user_status,
        "total":total
    }
    print(context)
    return render(request, 'expense_summary.html', context)

def process_emails(username,password,user):
    print(user)
    print(username)
    print(password)
   
    # Function to connect to the IMAP server
    def connect_to_imap(username, password):
        
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        
        mail.login(username, password)
        print("ssss", username , "ssss", password)

        return mail

    # Function to fetch emails from the inbox within the last 2 minutes
    def fetch_emails_within_last_day(mail):
        two_minutes_ago = datetime.now() - timedelta(days=1)
        date_two_minutes_ago = two_minutes_ago.strftime('%d-%b-%Y')
        mail.select('inbox')
        _, data = mail.search(None, f'(SINCE "{date_two_minutes_ago}")')
        email_ids = data[0].split()
        emails = []
        for email_id in email_ids:
            _, data = mail.fetch(email_id, '(RFC822)')
            emails.append((email_id, data[0][1]))
        return emails

    # Function to parse email content and extract relevant information
    def parse_email(email_content):
        msg = email.message_from_bytes(email_content)
        sender = msg['From']
        subject = msg['Subject']
        body = ""
        # received_at = parsedate_to_datetime(msg['Date'])

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        return {"sender": sender, "subject": subject, "body": body}

    # Function to identify order-related emails using regular expressions
    def identify_order_emails(emails):
        order_emails = []
        for email_id, email_content in emails:
            try:
                con = parse_email(email_content)
                if re.search(r'(order\s+(summary|confirmation)|order\s+placed)', con["subject"], re.IGNORECASE) or re.search(r'(order\s+(summary|confirmation)|order\s+placed)', con["body"], re.IGNORECASE):
                    order_emails.append((email_id, con))
            except:
                pass
        return order_emails

    def string_to_dict(string_data):
        string_data=string_data.strip('```')
        string_data.replace('```python\n', '')


    # Fixing the string (adding commas and quotes)
        fixed_string = string_data.replace("\n", ",\n")
        fixed_string = fixed_string.replace("{", "{\"")
        fixed_string = fixed_string.replace("}", "\"}")
        fixed_string = fixed_string.replace(":", "\":\"")
        fixed_string = fixed_string.replace(",\"", ",\"")
        fixed_string = fixed_string.replace(",\n\"", ",\n\"")

        # Remove ``` at the beginning and end
        fixed_string = fixed_string.strip("```")
        fixed_string.strip()
        
        fixed_string = fixed_string.split(" = ")
        fixed_string = fixed_string[0] if len(fixed_string) == 1 else fixed_string[1]
        fixed_string.strip()
        fixed_string = fixed_string.replace(r'{",','{')
        fixed_string = fixed_string.replace(r'"},','}')
        print("fs: ",fixed_string)
        print(type(fixed_string))
        data_string = fixed_string.replace('":', '":')

# Split the string by commas
        key_value_pairs = data_string.split(',')

        # Initialize an empty dictionary
        data_dict = {}

        # Iterate through each key-value pair
        for pair in key_value_pairs:
            print(pair)
            # Split the pair into key and value
            try:
                arr  = pair.split('":"')
                key =arr[0]
                if len(arr)>2:
                    value = ":".join(arr[1:])
                else:
                    value = arr[1]
                # Remove extra double quotes
                key = key.strip().strip('"').lower()
                value = value.strip().strip('"')
                if key == 'date/time':
                    value = value.split('.')[0]
                # Add key-value pair to dictionary
                data_dict[key] = value
            except:
                pass


     
        # Convert string to dictionary
        print(data_dict)
        return data_dict
    # Function to store emails in the Django model Email
    def store_emails_in_db(emails,user=user):
        for email_id, email_data in emails:
            Email.objects.create(
                email_id=email_id,  # Save email_id to identify emails uniquely
                user_id=User.objects.filter(pk=user).first(),
                sender=email_data["sender"],
                subject=email_data["subject"],
                body=email_data["body"],
                # received_at=email_data["received_at"]
                received_at=datetime.now()
            )

    # Function to process emails using Gemini
    def process_emails_with_gemini(user=user):
        # Configure Gemini connection (replace with your API key)
        genai.configure(api_key="")
        model = genai.GenerativeModel('gemini-pro')
        query_set = list(Email.objects.filter(processed=False,user_id=user).all())        
        print(query_set)
        for email_data in query_set :  # Only process emails not marked as processed
          
            gemini_prompt = f'''
                the Gemini will give me the user_id (same as given above) ,
                Sender_platform (the ecommerce platform name from where the order has been place: can be decoded by the senders email) ,
                sender_icon (a code to decode the e-commerce platform from the sender email and then in the table insert their respective icon) ,
                order_id ( any id/number that is given in the email as an order id) ,
                the product name ( identity the name of the product from the mail body if not identified any then save as ITEM) ,
                category ( try to classify the type of product as in a category , like electronics ,clothes ,homeware etc, If the product name is ITEM or not able to classify the product then save as OTHER) ,
                amount ( identify the total amount of the order from the email body, generally the max amount followed by the symbol Rs. ) ,
                date/time ( date/time of the order placed) ,
                status ( whether the order is confirmed, delivered, returned, also if the Gemini finds a email with same email order, then without adding a new row, only update this status )  ,
                feedback ( if there is a link in the body asking the user to give the feedback , then upload that link in this column , if nothing is given then keep it empty, return it in python dictionary format )
                '''+f"{email_data.email_id},{email_data.user_id},{email_data.sender},{email_data.subject},{email_data.body},{email_data.received_at}"

            response = model.generate_content(gemini_prompt)
            order_info = response.text.split("|")
           
            orde_dic = string_to_dict(order_info[0])
    # Fixing the string (adding commas and quotes
            print("od",orde_dic)
            keys = list(orde_dic.keys())
            print(keys)
            
            sender_platform = email_data.sender.split("@")[1].split(".")[0]
            user_id = email_data.user_id 
            order_id = orde_dic["order_id"] if "order_id" in keys else "_"
            product_name = orde_dic["product_name"] if "product_name" in keys else "_"
            category = orde_dic["category"] if "category" in keys else "_"
            # Handle potential conversion errors for amount
            amount = 0  # Default value if conversion fails
            if "amount" in keys and orde_dic["amount"] is not None:
                try:
                        amount = int(orde_dic["amount"])
                except ValueError:
        # Handle the case where orde_dic["amount"] is not a valid integer
        # For example, you could log an error message or take another appropriate action
                            pass

            # amount = int(orde_dic["amount"] if "amount" in keys and orde_dic["amount"] is not None else '0')
            # amount = int(orde_dic.get("amount", 0))
            # date_time_format = '%A %B %d %Y at %H":"%M'
            # date_time_format = '%Y-%m-%d %H:%M:%S.%f%z'    
            # date_time = datetime.strptime(orde_dic["date/time"],date_time_format) 
            try :
                if "date/time" in keys: 
                # date_time=date_time.strftime(r'%Y-%m-%d %H:%M:%S')
                    if '.' in orde_dic["date/time"] and '+' in orde_dic["date/time"]:
                        date_time_format = r'%Y-%m-%d %H:%M:%S.%f%z'
                    else:
                        date_time_format = r'%Y-%m-%d %H:%M:%S'
                
            
                date_time = datetime.strptime(orde_dic["date/time"], date_time_format)    
            except :
                date_time = datetime.now()
                date_time = date_time.strftime(r"%Y-%m-%d %H:%M:%S")
                    

# Parse the string to datetime object
                 
            status = orde_dic["status"] if "status" in keys else "_"
            feedback = orde_dic["feedback"] if "feedback" in keys else "_"
             
            

            # Store data in MailExpense model
            MailExpense.objects.create(
                user_id=User.objects.filter(pk=user).first(),
                platform=sender_platform,
                order_id=order_id,
                item=product_name,
                category=category,
                amount=amount,
                date_of_purchase=date_time,
                status=status,
                feedback=feedback
            )

            # Mark email as processed
            email_data.processed = True
            email_data.save()

    # Main function to process data and insert into the database

    def process_data_and_insert(username,password):
    # Fetching user credentials
            mail = connect_to_imap(username, password)
            
            emails = fetch_emails_within_last_day(mail)
            
            # print(emails)
            order_emails = identify_order_emails(emails)
            print(order_emails)
            store_emails_in_db(order_emails)
            process_emails_with_gemini(user)

    process_data_and_insert(username, password)
    return True

   
# def process_emails_view(request):
#     if request.method == 'POST':
#         # Assuming username and password are passed in the request
#         username = request.POST.get('gmail')
#         password = request.POST.get('app_password')
        # request.POST.get('password')
# def process_emails_view(request):
#     if request.method == 'POST':
#         # Assuming username and password are passed in the request
#         username = request.POST.get('gmail')
#         password = request.POST.get('app_password')
#         # request.POST.get('password')

#         # Trigger the Celery task
#         process_emails.delay(username, password)

#         return JsonResponse({'message': 'Email processing started successfully.'},status=200)
#     else:
#         return JsonResponse({'error': 'Only POST requests are allowed.'}, status=400)


@api_view(["POST"])
def mail_expenses_view(request):
    data = request.data
    print(data)
    # email = data["email"]
    user_id = data["user_id"]
    # Check if the user exists based on the provided email
    try:
        # user = User.objects.get(gmail=email)
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Obtain the user_id directly from the user object
    user_id = user.pk
    print(user_id)
    apppassword = User.objects.get(user_id=user_id).app_password
    gmail= User.objects.get(user_id=user_id).gmail
    # password = data["password"]
    process = process_emails(gmail, apppassword, user_id)
    
    # Assuming process_emails function returns a boolean indicating success or failure
    if process:
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({"message": "Failed to process emails"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# def mail_expenses_view(request):
#     if request.method == 'POST':
#         # Extract user_id from the request body
#         user_id = request.POST.get('id')

#         if not user_id:
#             return JsonResponse({"error": "User ID is required"}, status=400)
#         try:
#             user = User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return JsonResponse({"error": "User not found"}, status=404)

#         gmail = user.gmail
#         apppassword = user.app_password

#         # Assuming process_emails function returns a boolean indicating success or failure
#         process_success = process_emails(gmail, apppassword, user)

#         if process_success:
#             # Fetch mail expenses for the user and return as JSON
#             expenses = MailExpense.objects.filter(user_id=user_id).values()
#             return JsonResponse({"expenses": list(expenses)})
#         else:
#             return JsonResponse({"error": "Failed to process emails"}, status=500)
#     else:
#         return JsonResponse({"error": "Method not allowed"}, status=405)



# class MailExpensesView(TemplateView):
#     template_name = 'mail_expenses.html'

#     def post(self, request, *args, **kwargs):
#         data = request.POST

#         # Ensure that 'id' is present in the request data
#         if 'id' not in data:
#             return HttpResponse("User ID is required", status=400)

#         user_id = data["id"]

#         try:
#             # Check if the user exists based on the provided user_id
#             user = User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return HttpResponse("User not found", status=404)

#         # Retrieve user's email and app_password
#         gmail = user.gmail
#         apppassword = user.app_password

#         # Call process_emails function
#         process = process_emails(gmail, apppassword, user_id)

#         # Assuming process_emails function returns a boolean indicating success or failure
#         if process:
#             return HttpResponse(status=204)
#         else:
#             return HttpResponse("Failed to process emails", status=500)
# def create_user(request):
#     # Generate a random 4-digit user_id
#     user_id = random.randint(1000, 9999)
#     # Ensure user_id doesn't already exist
#     while User.objects.filter(user_id=user_id).exists():
#         user_id = random.randint(1000, 9999)
    
#     # Other user data
#     user_name = "Sample User"  # You can replace this with actual user data
#     phone_number = "1234567890"  # You can replace this with actual user data
#     gmail = "example@example.com"  # You can replace this with actual user data
#     login_password = "password"  # You can replace this with actual user data
#     app_password = "app_password"  # You can replace this with actual user data

#     # Create the user
#     user = User.objects.create(
#         user_id=user_id,
#         user_name=user_name,
#         phone_number=phone_number,
#         gmail=gmail,
#         login_password=login_password,
#         app_password=app_password
#     )

#     return HttpResponse(f"User created with user_id: {user_id}")


def sign_up(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # Check if a user with the given email already exists
            email = form.cleaned_data['gmail']
            if User.objects.filter(gmail=email).exists():
                messages.error(request, 'User with this email already exists.')
            else:
                # Save the user
                user = form.save(commit=False)
                user.user_id = User.generate_unique_user_id()
                user.save()
                user_status = UserStatus(user=user)
                user_status.save()
                return redirect('/login')  # Redirect to homepage or any other desired page
        else:
            # Form is not valid, return form along with error messages
            messages.error(request, 'Invalid form data. Please correct the errors below.')
    else:
        form = UserForm()
    return render(request, 'signup.html', {'form': form})



@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('gmail')
        login_password = request.POST.get('login_password')
        user = User.objects.filter(gmail=email, login_password=login_password).first()
        print(user)
        if user :
            # login(request, user)
            # Django's built-in authentication system automatically updates the last_login time
            resp = redirect('index')  # Redirect to home or wherever after login
            resp.set_cookie("email",email)
            resp.set_cookie("id",user.user_id)
            return resp
        else:
            # If authentication fails, return 401 Unauthorized status code
            return HttpResponse("Unauthorized", status=401)
    
    form = LoginForm()
    rsp= render(request, 'login.html', {'form':form, 'title':'log in'})
    return rsp


def index(request):
    return render(request, 'index.html')

# def my_view(request):
    # Your view logic here
    return render(request, 'index.html', {'user': request.user})

def format_expenses_as_table(expenses):
    # Define headers for the table
    headers = ["Item", "Amount", "Category", "Date"]

    # Create a list to hold each row of data
    table_data = []

    # Append headers as the first row of the table
    table_data.append(headers)

    # Iterate over each expense object and append its attributes as a row in the table
    for expense in expenses:
        row = [expense.item, expense.amount, expense.category, expense.date]
        table_data.append(row)

    # Calculate the maximum width of each column
    col_widths = [max(len(str(row[i])) for row in table_data) for i in range(len(headers))]

    # Format the table
    formatted_table = ""
    for row in table_data:
        formatted_table += "|".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(headers))) + "\n"

    return formatted_table

def format_user_status_table(user_status):
    # usd = dict(user_status)
    # Initialize the header and separator
    table = "Attribute            | Value\n"
    # keys = usd.keys()

    # Iterate over each field in the UserStatus model
    for field in user_status._meta.fields:

        # Format the field name and value

        field_name = field.name
         
        field_value = getattr(user_status, field_name)

        
        # Add the field name and value to the table
        table += f"{field_name.ljust(20)}| {field_value}\n"

    return table

def chatbot_view(request):
    conversation=request.session['conversation']
    expenses = Expense.objects.all()
    if request.method == 'POST':
        user_input = request.POST.get('user_input')

        # Append user input to the conversation
        if user_input:
            conversation.append({"role": "user", "content": user_input})

        # Define the API endpoint and parameters
        api_endpoint = "https://api.openai.com/v1/chat/completions"
        api_key =  ""   # Replace with your actual API key
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": conversation
        }

        # Make a POST request to the API
        response = requests.post(api_endpoint, json=data, headers=headers)
        print(response)
        # Extract chatbot replies from the API response
        if response.status_code == 200:
            chatbot_replies = [message['message']['content'] for message in response.json()['choices'] if message['message']['role'] == 'assistant']
            # Append chatbot replies to the conversation
            for reply in chatbot_replies:
                conversation.append({"role": "assistant", "content": reply})

            # Update the conversation in the session
            request.session['conversation'] = conversation
            
    # Render the template with the updated conversation
    
    return render(request, 'index.html', {'conversation': request.session['conversation'], 'expenses': expenses})


def comparepredict(request):
    context = {
        'variable': ''
    }
    if request.method == 'POST':
        # Retrieve the values of product name and date from the POST request
        product_name = request.POST.get('productName')
        date = request.POST.get('date')
        comparison_result = compare_p(product_name)
        # Log the product name and date
        print("Product Name:", product_name)
        print("Date:", date)

        # API CALL TO GET PRICE HISTORY
        product_gtin = {
            'dell laptop': '0195908483175',
            'hp mouse': '0195908483175',
            'sony headphones': '4905524731903',
            'samsung galaxy s21': '8806090886713',
            'apple macbook air': '0194252058503',
            'microsoft surface pro': '0889842192940',
            'black dress': '8804775088735',
            'study table': '6900075928046',
            'formal shirt': '7320545206747',
            'casio fx': '4549526613029',
            'pencil stand': '6953156278554',
            'electric kettle': '5412810270316',
            'smart watch': '4047443489012',
            'first aid box': '7310802909009',
            'extension cord': '4008297056973',
            'realme charger': '8596311135736',
            'nike shoes': '0196149620046',
            'iphone 15':'195949050008',
        }

        # Function to look up GTIN based on product name
        def get_gtin(product_name):
            product_name = product_name.lower()
            if product_name in product_gtin:
                return product_gtin[product_name]
            else:
                return "6900075928046"
            
        gtincode = get_gtin(product_name)

        print("GTIN Code:", gtincode)

        url = "https://product-price-history.p.rapidapi.com/price-history"

        querystring = {"country_iso2":"nl","gtin":gtincode,"last_x_months":"24"}

        headers = {
            'X-RapidAPI-Key': 'ce0e549619msh13a1619e4132572p1965f6jsn5095b54e28d8',
            'X-RapidAPI-Host': 'product-price-history.p.rapidapi.com'
        } 

        response = requests.get(url, headers=headers, params=querystring)

        priceHistory = response.json()

        print(response.json())


        #TESTING CODE FOR COST PREDICTION

        # Assuming you have the JSON data stored in a variable named 'json_data'
        # Load data from JSON
        data = priceHistory

        # Extract timestamps and average prices
        timestamps = []
        avg_prices = []
        if type(data) == dict:

            for timestamp, info in list(data.items()):
                timestamps.append(info['key'])  # Assuming 'key' is the numerical representation of the timestamp
                avg_prices.append(info['avg_price_in_cents'])

            # Convert timestamps into a 2D array
            X = np.array(timestamps).reshape(-1, 1)

            # Convert average prices into a 1D array
            y = np.array(avg_prices)

            # Split data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train linear regression model
            model = LinearRegression()
            model.fit(X_train, y_train)

            # Evaluate model
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            print("Mean Squared Error:", mse)

            # Function to predict price for a specific date
            def predict_price_for_date(date):
                # Convert date to timestamp
                timestamp = int(date.timestamp())
                # Predict price using the model
                predicted_price = model.predict(np.array([[timestamp]]))
                return predicted_price

            # Example: Predict price for August 19, 2025
            input_date = datetime(2025, 8, 19)
            predicted_price = predict_price_for_date(input_date)

            predicted_price = predicted_price * 0.0542

            print("Predicted price for", input_date.strftime('%Y-%m-%d'), ":", predicted_price)
            
            # Return a JSON response indicating successful logging
            # return JsonResponse({'message': 'Data logged successfully'})

            # MINIMUM AND MAXIMUM PRICE MONTH PREDICTION

            # Group data by month
            print("Data is fine here : ", data)
            monthly_data = defaultdict(list)
            for date_str, info in data.items():
                month = date_str[:7]
                monthly_data[month].append(info)
            
            # Calculate total purchases and average price for each month
            result = {}
            for month, purchases in monthly_data.items():
                total_purchases = sum(info['data_points'] for info in purchases)
                avg_price = sum(info['avg_price_in_cents'] * info['data_points'] for info in purchases) / total_purchases
                result[month] = {'total_purchases': total_purchases, 'avg_price': avg_price}
            
            # Find the month with maximum purchases and lowest average price
            max_purchases_month = max(result, key=lambda m: result[m]['total_purchases'])
            lowest_avg_price_month = min(result, key=lambda m: result[m]['avg_price'])

            print("Month with maximum purchases:", max_purchases_month)
            print("Month with lowest average price:", lowest_avg_price_month)

            context = {
                'variable': predicted_price,
                'max_purchases_month': max_purchases_month,
                'lowest_avg_price_month': lowest_avg_price_month,
                'comparison_result': comparison_result
            }
        else:
            context = {
                'variable': "not found",
                'max_purchases_month': "not found",
                'lowest_avg_price_month': "not found",
                'comparison_result': "not found",
            }
        
    return render(request, 'comparison.html', context)


