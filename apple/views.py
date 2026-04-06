import random
import time
import re

from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def safe_flush(request):
    if request.session.exists(request.session.session_key):
        request.session.flush()


def email_send(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render(request, "email_send.html", {
                "error": "Enter valid email"
            })

        otp = random.randint(100000, 999999)

        safe_flush(request)

        request.session['email'] = email
        request.session['otp'] = str(otp)
        request.session['otp_time'] = time.time()
        request.session['otp_attempts'] = 0

        send_modern_email(email, otp)

        return redirect('verify')

    return render(request, "email_send.html")


def verify_otp(request):
    email = request.session.get('email')

    if not email:
        return redirect('email_send')

    if time.time() - request.session.get('otp_time', 0) > 120:
        safe_flush(request)
        return render(request, "email_verification.html", {
            "expired": True,
            "email": email
        })

    if request.method == "POST":
        user_otp = request.POST.get("otp", "").strip()
        attempts = request.session.get('otp_attempts', 0) + 1

        if attempts > 5:
            safe_flush(request)
            return render(request, "email_verification.html", {
                "error": "Too many attempts"
            })

        if user_otp == request.session.get("otp"):
            safe_flush(request)
            return render(request, "success.html")

        request.session['otp_attempts'] = attempts

        return render(request, "email_verification.html", {
            "error": "Invalid OTP",
            "attempts_left": 5 - attempts
        })

    return render(request, "email_verification.html", {
        "email": email
    })


def resend_otp(request):
    email = request.session.get('email')

    if email:
        otp = random.randint(100000, 999999)

        request.session['otp'] = str(otp)
        request.session['otp_time'] = time.time()
        request.session['otp_attempts'] = 0

        send_modern_email(email, otp)

    return redirect('verify')


import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_modern_email(email, otp):
    message = Mail(
        from_email=os.environ.get("EMAIL_HOST_USER"),
        to_emails=email,
        subject="Your OTP Code",
        html_content=f"<strong>Your OTP is {otp}</strong>"
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(message)
        print("✅ Email sent via SendGrid")
    except Exception as e:
        print("❌ Email failed:", str(e))