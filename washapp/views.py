from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout
from datetime import date

from .models import *
from .forms import UserRegistrationForm


# =========================
# HOME & AUTH
# =========================

def home(request):
    services = Service.objects.all()[:6]
    return render(request, 'home.html', {'services': services})


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


# =========================
# DASHBOARD
# =========================

@login_required
def dashboard(request):
    user = request.user

    # ADMIN DASHBOARD
    if user.user_type == 'admin':
        return render(request, 'admin_dashboard.html', {
            'total_users': User.objects.count(),
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'total_revenue': sum(
                b.total_amount for b in Booking.objects.filter(status='completed')
            ),
            'recent_bookings': Booking.objects.order_by('-created_at')[:10],
        })

    # CUSTOMER DASHBOARD
    bookings = Booking.objects.filter(customer=user)
    return render(request, 'customer_dashboard.html', {
        'bookings': bookings,
        'total_bookings': bookings.count(),
    })


# =========================
# BOOKINGS
# =========================

@login_required
def book_service(request):
    if request.method == 'POST':
        service = get_object_or_404(Service, id=request.POST.get('service_id'))
        provider = ServiceProvider.objects.filter(services=service).first()

        if not provider:
            messages.error(request, 'No provider available')
            return redirect('book_service')

        Booking.objects.create(
            customer=request.user,
            service=service,
            service_provider=provider,
            booking_date=request.POST.get('booking_date'),
            booking_time=request.POST.get('booking_time'),
            vehicle_type=request.POST.get('vehicle_type'),
            vehicle_number=request.POST.get('vehicle_number'),
            total_amount=service.price,
            status='pending'
        )

        messages.success(request, 'Booking successful!')
        return redirect('my_bookings')

    return render(request, 'booking/book_service.html', {
        'services': Service.objects.all(),
        'today': date.today()
    })


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(customer=request.user)
    return render(request, 'my_bookings.html', {'bookings': bookings})


@login_required
def booking_details(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'booking/details.html', {'booking': booking})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    booking.status = 'cancelled'
    booking.save()
    messages.success(request, 'Booking cancelled')
    return redirect('my_bookings')


# =========================
# SERVICES & STATIC PAGES
# =========================

def services_list(request):
    return render(request, 'services.html', {
        'services': Service.objects.all(),
        'categories': ServiceCategory.objects.all()
    })


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


def faq(request):
    return render(request, 'faq.html')


# =========================
# PROFILE
# =========================

@login_required
def profile(request):
    return render(request, 'profile.html')


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')

    return redirect('profile')


# =========================
# REVIEWS
# =========================

@login_required
def add_review(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user,
        status='completed'
    )

    if request.method == 'POST':
        Review.objects.create(
            booking=booking,
            customer=request.user,
            rating=request.POST.get('rating'),
            comment=request.POST.get('comment', '')
        )

        messages.success(request, 'Review submitted successfully!')
        return redirect('my_bookings')

    return render(request, 'booking/review.html', {'booking': booking})


# =========================
# PROVIDER
# =========================

@login_required
def provider_registration(request):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'This page is only for service providers')
        return redirect('dashboard')

    if ServiceProvider.objects.filter(user=request.user).exists():
        messages.info(request, 'Provider registration already completed')
        return redirect('dashboard')

    if request.method == 'POST':
        provider = ServiceProvider.objects.create(
            user=request.user,
            company_name=request.POST.get('company_name'),
            address=request.POST.get('address'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email', request.user.email)
        )

        provider.services.set(
            Service.objects.filter(id__in=request.POST.getlist('services'))
        )

        messages.success(request, 'Provider registration completed!')
        return redirect('dashboard')

    return render(request, 'registration/provider_registration.html', {
        'services': Service.objects.all()
    })


@login_required
def update_booking_status(request, booking_id):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Only service providers can update booking status')
        return redirect('dashboard')

    provider = get_object_or_404(ServiceProvider, user=request.user)
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        service_provider=provider
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, 'Booking status updated')
        else:
            messages.error(request, 'Invalid status')

    return redirect('dashboard')
