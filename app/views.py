from django.shortcuts import render
from .auth import authentication 
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from app import views
from django.contrib.auth.decorators import login_required
import pandas as pd
import numpy as np
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from keras.models import Sequential
from keras.layers import Dense
from sklearn.metrics import accuracy_score
from django.http import HttpResponse
import matplotlib.pyplot as plt
import io, base64
from django.core.mail import send_mail

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == "POST":
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        username = request.POST.get('username')   # email as username
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        if password != cpassword:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "User already exists!")
            return redirect("register")

        # Create Django User
        user = User.objects.create_user(username=username, password=password,
                                        first_name=fname, last_name=lname, email=username)


        messages.success(request, "Registration Successfully.")
        return redirect("log_in")

    return render(request, "register.html")


def log_in(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect("log_in")

    return render(request, "log_in.html")



def dashboard(request):
    return render(request, "dashboard.html")

churned_customers = None

import pandas as pd
import numpy as np
import io
import base64
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
from django.core.files.storage import FileSystemStorage

# Global variable to store churned customers for download
churned_customers = None

def upload_file(request):
    context = {}
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        file_path = fs.save(uploaded_file.name, uploaded_file)

        # Load dataset
        dataset = pd.read_csv(fs.path(file_path))

        # Drop empty rows
        dataset = dataset.dropna()

        # Drop unnatural ID columns
        id_columns = [col for col in dataset.columns if 'id' in col.lower()]
        if id_columns:
            dataset = dataset.drop(columns=id_columns)

        # Detect churn column
        target_col = None
        for col in dataset.columns:
            if 'churn' in col.lower() or 'exited' in col.lower():
                target_col = col
                break

        if not target_col:
            messages.error(request, "No churn column found in dataset. Please ensure column name contains 'churn' or 'exited'.")
            return redirect("dashboard")

        # Split features/labels
        X = dataset.drop(columns=[target_col])
        y = dataset[target_col]

        # Label encode categorical data
        le = LabelEncoder()
        for col in X.select_dtypes(include=['object']).columns:
            X[col] = le.fit_transform(X[col].astype(str))

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale numeric features only
        numeric_cols = X_train.select_dtypes(include=np.number).columns
        scaler = StandardScaler()
        X_train[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
        X_test[numeric_cols] = scaler.transform(X_test[numeric_cols])

        # ML MODEL - Random Forest
        rf = RandomForestClassifier(n_estimators=300, random_state=42)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_acc = accuracy_score(y_test, rf_pred) * 100

        # DEEP LEARNING MODEL
        model = Sequential([
            Dense(128, activation='relu', input_dim=X_train.shape[1]),
            Dense(64, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X_train, y_train, epochs=15, batch_size=32, verbose=0)
        dl_acc = model.evaluate(X_test, y_test, verbose=0)[1] * 100

        # Predict churn for entire dataset using Random Forest (more interpretable)
        X_scaled = X.copy()
        X_scaled[numeric_cols] = scaler.transform(X[numeric_cols])
        dataset['Predicted_Churn'] = rf.predict(X_scaled)

        # Save churned customers globally for download
        global churned_customers
        churned_customers = dataset[dataset['Predicted_Churn'] == 1].copy()

        # === Find common columns safely ===
        tenure_col = next((col for col in dataset.columns if 'tenure' in col.lower()), None)
        balance_col = next((col for col in dataset.columns if 'balance' in col.lower()), None)
        age_col = next((col for col in dataset.columns if 'age' in col.lower()), None)

        # Fallback to first few columns if not found
        if not tenure_col and len(dataset.columns) > 1:
            tenure_col = dataset.columns[1]
        if not balance_col and len(dataset.columns) > 2:
            balance_col = dataset.columns[2]
        if not age_col and len(dataset.columns) > 0:
            age_col = dataset.columns[0]

        # Reset index for plotting
        dataset = dataset.reset_index(drop=True)
        dataset['Index'] = dataset.index

        # === Generate Interactive Plotly Charts ===

        # 1. Pie Chart
        pie_fig = px.pie(
            values=[len(churned_customers), len(dataset) - len(churned_customers)],
            names=['Churned', 'Retained'],
            color_discrete_sequence=['#ff6b6b', '#4ecdc4'],
            hole=0.4
        )
        pie_fig.update_traces(textinfo='percent+label', textposition='inside')
        pie_fig.update_layout(title="Churn Rate Distribution", template="plotly_dark")
        pie_chart = plot(pie_fig, output_type='div', include_plotlyjs=False)

        # 2. Bar Chart
        bar_fig = go.Figure(data=[
            go.Bar(name='Retained', x=['Status'], y=[len(dataset) - len(churned_customers)], marker_color='#00b894'),
            go.Bar(name='Churned', x=['Status'], y=[len(churned_customers)], marker_color='#e17055')
        ])
        bar_fig.update_layout(title="Churned vs Retained Customers", barmode='stack', template="plotly_dark")
        bar_chart = plot(bar_fig, output_type='div', include_plotlyjs=False)

        # 3. Histogram (Tenure Distribution by Churn)
        hist_fig = px.histogram(
            dataset, x=tenure_col, color='Predicted_Churn',
            color_discrete_map={0: '#74b9ff', 1: '#fab1a0'},
            nbins=20, barmode='overlay', opacity=0.8,
            title=f"Distribution of {tenure_col} by Churn Status"
        )
        hist_fig.update_layout(template="plotly_dark", bargap=0.1)
        histogram = plot(hist_fig, output_type='div', include_plotlyjs=False)

        # 4. Scatter Plot (Age vs Balance)
        scatter_fig = px.scatter(
            dataset, x=age_col, y=balance_col, color='Predicted_Churn',
            color_discrete_map={0: '#55efc4', 1: '#fd79a8'},
            size_max=10, opacity=0.7,
            title="Age vs Balance - Churn Risk Insights"
        )
        scatter_fig.update_layout(template="plotly_dark")
        scatter = plot(scatter_fig, output_type='div', include_plotlyjs=False)

        # 5. Box Plot
        box_fig = px.box(
            dataset, x='Predicted_Churn', y=balance_col,
            color='Predicted_Churn',
            color_discrete_map={0: '#a29bfe', 1: '#fd79a8'},
            title=f"{balance_col} Distribution by Churn Status"
        )
        box_fig.update_layout(template="plotly_dark")
        box_plot = plot(box_fig, output_type='div', include_plotlyjs=False)

        # 6. Area Chart - Cumulative Churn
        area_data = dataset.sort_values('Index').copy()
        area_data['Cumulative_Churn'] = area_data['Predicted_Churn'].cumsum()
        area_fig = px.area(
            area_data, x='Index', y='Cumulative_Churn',
            title="Cumulative Churn Trend",
            color_discrete_sequence=['#e056fd']
        )
        area_fig.update_layout(template="plotly_dark")
        area_chart = plot(area_fig, output_type='div', include_plotlyjs=False)

        # === Context to send to template ===
        context = {
            'rf_acc': round(rf_acc, 2),
            'dl_acc': round(dl_acc, 2),
            'total': len(dataset),
            'churned': len(churned_customers),
            'retained': len(dataset) - len(churned_customers),
            'pie_chart': pie_chart,
            'bar_chart': bar_chart,
            'histogram': histogram,
            'scatter': scatter,
            'box_plot': box_plot,
            'area_chart': area_chart,
        }

        return render(request, 'result.html', context)

    return render(request, 'dashboard.html', context)

def download_churn_customers(request):
    global churned_customers
    if churned_customers is not None:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="churned_customers.xlsx"'
        churned_customers.to_excel(response, index=False)
        return response
    return HttpResponse("No churned customers found!")

def log_out(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("/")





@login_required
def send_email(request):
    if request.method == "POST":
        message = request.POST.get("message", "")
        customer_type = request.POST.get("customer_type", "")

        user_email = request.user.email or request.user.username or "your_email@example.com"
        subject = f"Churn Analysis Report - {customer_type.capitalize() if customer_type else 'General'}"

        try:
            print("=== EMAIL DEBUG ===")                    # ← Debug
            print(f"Subject: {subject}")
            print(f"To: {user_email}")
            print(f"Message length: {len(message)}")

            send_mail(
                subject=subject,
                message=message,
                from_email="kothmirehitesh.1219@gmail.com",
                recipient_list=[user_email],
                fail_silently=False,
            )
            messages.success(request, f"Email sent successfully to {user_email}!")
            print("✅ Email sent successfully!")

        except Exception as e:
            error_msg = str(e)
            print("❌ EMAIL ERROR:", error_msg)           # ← This will show in terminal
            messages.error(request, f"Failed to send email: {error_msg}")

    return redirect("dashboard")