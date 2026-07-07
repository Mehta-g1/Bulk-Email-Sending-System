from django.core.mail import send_mail, EmailMultiAlternatives
from .models import emailUsers, Receipent, reset_link
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404
from EmailTemplates.models import Template
from django.contrib import messages
from django.db import transaction
from django.contrib.sites.shortcuts import get_current_site
import pandas as pd
import re
import logging

# Configure Logger
logger = logging.getLogger(__name__)

def profileCompletetion(user):
    total_fields,filled_fields,=12,0
    fields_to_check = [
        user.name,
        user.email_address,
        user.post,
        user.department,
        user.about_you,
        user.personalEmail,
        user.org_name,
        user.dob,
        user.address,
        user.phone,
        user.email_password,
        user.image if user.image and user.image.name != 'default.png' else None
    ]

    # Count filled fields
    for field in fields_to_check:
        if field not in [None, '', 'default.png']:
            filled_fields += 1

    # Calculate completion percentage
    completion_percentage = (filled_fields / total_fields) * 100
    return int(completion_percentage)


# Utilities functions

def send_forget_password_link(request, user_email, token):
    """
    Sends a password reset link to the given user email.
    Uses dynamic domain from request.
    """
    current_site = get_current_site(request)
    domain = current_site.domain
    protocol = 'https' if request.is_secure() else 'http'
    
    reset_link = f"{protocol}://{domain}/user/reset-password/{token}/"

    subject = "Reset Your Password"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    # Plain text fallback (in case user's email doesn't support HTML)
    text_content = f"Please reset your password using the following link: {reset_link}"

    # HTML content
    html_content = f"""
    <html>
    <body>
        <p>We received a request to reset your password.</p>
        <p>
            <a href="{reset_link}" style="
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #007bff;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 0;
            ">Reset Password</a>
        </p>
        <p>If you did not request this, you can safely ignore this email.</p>
        <p>Thanks,<br>Email Sender Team</p>
    </body>
    </html>
    """

    # Create email
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def check_token(token):
    Token = get_object_or_404(reset_link, token = token)
    if not Token:
        logger.warning("Invalid Token accessed")
        return False
    if Token.is_attempted:
        logger.warning("Attempted to use already used token")
        return False
    timediff = now() - Token.datetime  
    logger.info(f"Token check: Sending time: {Token.datetime}, Current time: {now()}, Diff: {timediff}")
    
    if timediff > timedelta(minutes=15):
        return False
    return True

def is_validEmail(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.fullmatch(pattern, email):
        return True
    return False


def extract_receipients_from_file(user, file, group,  request):
    if not file.file:
        messages.warning(request, "No file found or corrupted file. Please upload again CSV/XLS/XLSX file.")
        return False
    
    try:
        # Determine file path
        file_path = file.file.path
        if file.file_type.lower() == 'csv':
            # Try reading with header first
            df = pd.read_csv(file_path)
            # Check if headers actually look like headers or data
            # If the first row (headers) contains an email-like string, it might be headerless
            first_row_str = ' '.join(df.columns.astype(str))
            if '@' in first_row_str and '.' in first_row_str:
                df = pd.read_csv(file_path, header=None)
        else:
            df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        messages.warning(request, "There was an error reading the file. Please ensure it is a valid CSV/XLS/XLSX file.")
        return False
        
    try:
        # Normalize columns to lowercase strings
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # 1. Try Smart Column Matching (by header name)
        name_col = next((c for c in df.columns if c in ['name', 'fullname', 'user', 'username', 'client', 'customer']), None)
        email_col = next((c for c in df.columns if c in ['email', 'email_address', 'e-mail', 'mail']), None)
        category_col = next((c for c in df.columns if c in ['category', 'type', 'designation']), None)
        comment_col = next((c for c in df.columns if c in ['comment', 'comments', 'description', 'remark']), None)

        # 2. Heuristic Fallback (if headers don't match or are numeric)
        if not email_col:
            # Look for the first column where the first non-null value looks like an email
            for col in df.columns:
                try:
                    first_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else ""
                    if '@' in first_val and '.' in first_val:
                        email_col = col
                        break
                except: continue
        
        if not name_col and email_col is not None:
            # If we found email but not name, assume the column before email is Name
            try:
                col_idx = list(df.columns).index(email_col)
                if col_idx > 0:
                    name_col = df.columns[col_idx - 1]
                elif len(df.columns) > 1:
                    name_col = df.columns[col_idx + 1]
            except: pass

        # 3. Final Fallback (Index based)
        if not email_col and len(df.columns) >= 2:
            name_col, email_col = df.columns[0], df.columns[1]
        elif not email_col and len(df.columns) == 1:
            email_col = df.columns[0]

        # Check critical columns
        if not email_col:
            messages.error(request, "Could not identify an 'Email' column. Please check your file headers.")
            return False

        added_count = 0
        skipped_count = 0
        duplicate_count = 0
        
        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    email = str(row[email_col]).strip() if pd.notna(row[email_col]) else ""
                    if not email or '@' not in email or '.' not in email:
                        skipped_count += 1
                        continue
                    
                    name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else "Customer"
                    if not name or name.lower() == 'nan': name = "Customer"
                    
                    category = str(row[category_col]).strip() if category_col and pd.notna(row[category_col]) else 'N/A'
                    if not category or category.lower() == 'nan': category = 'N/A'
                    
                    comments = str(row[comment_col]).strip() if comment_col and pd.notna(row[comment_col]) else ''
                    if not comments or comments.lower() == 'nan': comments = ''

                    # Check for duplicates in this group
                    if Receipent.objects.filter(Sender=user, email=email, group=group).exists():
                        duplicate_count += 1
                        continue

                    Receipent.objects.create(
                        Sender=user,
                        name=name,
                        email=email,
                        receipent_category=category,   
                        comment=comments,              
                        source=f"File - {file.file_name}",
                        group=group
                    )
                    added_count += 1
                except:
                    skipped_count += 1
        
        if added_count > 0:
            res_msg = f"Successfully added {added_count} recipients."
            if skipped_count > 0: res_msg += f" {skipped_count} invalid rows skipped."
            if duplicate_count > 0: res_msg += f" {duplicate_count} duplicates ignored."
            messages.success(request, res_msg)
            return True
        else:
            messages.warning(request, "No new recipients were added. Please check your file content.")
            return False

    except Exception as e:
        logger.error(f"Error extracting recipients: {e}")
        messages.error(request, f"An unexpected error occurred while processing the file: {e}")
        return False


def send_welcome_message(user, request):
    current_site = get_current_site(request)
    domain = current_site.domain
    protocol = 'https' if request.is_secure() else 'http'
    subject = "Welcome to Email Sender 🚀"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user.email_address]

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Welcome to <strong>EmailAuto - Advanced Email Automation & API Ecosystem</strong> 🚀</h2>

        <p>Hi <strong>{user.name}</strong>,</p>

        <p>
            Your account has been successfully created on <strong>EmailAuto</strong>.
            You can now start managing and sending bulk emails with ease.
        </p>

        <ul>
            <li>Add and manage recipients</li>
            <li>Create reusable email templates</li>
            <li>Send bulk emails using your own email account</li>
        </ul>

        <p>
            👉 <a href="http://{domain}/user/login/" target="_blank">
                Click here to login to your dashboard
            </a>
        </p>

        <p style="margin-top: 20px;">
            If you did not create this account, you can safely ignore this email.
        </p>

        <p>
            Thanks,<br>
            <strong>EmailAuto Team</strong>
        </p>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, html_content, from_email, to_email)
    msg.attach_alternative(html_content,"text/html")
    msg.send()
    messages.success(request, "Welcome Message Sent !")
    return True
