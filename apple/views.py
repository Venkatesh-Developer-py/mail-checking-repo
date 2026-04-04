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


def send_modern_email(email, otp):
    subject = "Your OTP Code"
    from_email = settings.EMAIL_HOST_USER

    text_content = f"Your OTP is {otp}"

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
        msg.send(fail_silently=True)  # 🔥 prevents crash
        print("Email sent")
    except Exception as e:
        print("Email failed:", e)