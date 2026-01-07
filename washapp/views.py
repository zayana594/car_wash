from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import *
from .forms import UserRegistrationForm  # You'll need to create this form
from datetime import date

def register(request):
    """User registration with custom User model"""
    if request.method == 'POST':
        # Use the form for validation
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Login the user
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Dirty to Clean!')
            
            # Redirect based on user type
            if user.user_type == 'service_provider':
                messages.info(request, 'Please complete your provider profile')
                return redirect('provider_registration')
            return redirect('dashboard')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Also update the home function to remove duplicate function
def home(request):
    """Home page"""
    try:
        services = Service.objects.all()[:6]
    except:
        services = []
    
    return render(request, 'home.html', {
        'services': services
    })

@login_required
def dashboard(request):
    """Dashboard view"""
    user = request.user
    
    # Now user has user_type attribute from your custom User model
    if user.user_type == 'customer':
        try:
            bookings = Booking.objects.filter(customer=user).order_by('-created_at')[:5]
            total_bookings = Booking.objects.filter(customer=user).count()
            upcoming_bookings = Booking.objects.filter(customer=user, status__in=['pending', 'confirmed']).count()
            completed_bookings = Booking.objects.filter(customer=user, status='completed').count()
            
            # Calculate total spent
            completed_booking_amounts = Booking.objects.filter(
                customer=user, 
                status='completed'
            ).values_list('total_amount', flat=True)
            total_spent = sum(completed_booking_amounts) if completed_booking_amounts else 0
            
            next_booking = Booking.objects.filter(
                customer=user, 
                status__in=['pending', 'confirmed']
            ).order_by('booking_date', 'booking_time').first()
            
        except Exception as e:
            bookings = []
            total_bookings = 0
            upcoming_bookings = 0
            completed_bookings = 0
            total_spent = 0
            next_booking = None
        
        # Add status color and icon to bookings
        for booking in bookings:
            if booking.status == 'completed':
                booking.status_color = 'success'
                booking.status_icon = 'check-circle'
            elif booking.status == 'pending':
                booking.status_color = 'warning'
                booking.status_icon = 'clock'
            elif booking.status == 'confirmed':
                booking.status_color = 'info'
                booking.status_icon = 'check'
            elif booking.status == 'in_progress':
                booking.status_color = 'primary'
                booking.status_icon = 'spinner'
            elif booking.status == 'cancelled':
                booking.status_color = 'danger'
                booking.status_icon = 'times-circle'
            else:
                booking.status_color = 'secondary'
                booking.status_icon = 'question-circle'
        
        return render(request, 'customer_dashboard.html', {
            'bookings': bookings,
            'total_bookings': total_bookings,
            'upcoming_bookings': upcoming_bookings,
            'completed_bookings': completed_bookings,
            'total_spent': total_spent,
            'next_booking': next_booking,
            'recent_bookings': bookings[:5],  # Show first 5 as recent
        })
    
    elif user.user_type == 'service_provider':
        try:
            provider = ServiceProvider.objects.get(user=user)
            provider_bookings = Booking.objects.filter(service_provider=provider)
            
            # Provider stats
            total_bookings = provider_bookings.count()
            today = datetime.date.today()
            today_bookings = provider_bookings.filter(booking_date=today).count()
            pending_bookings = provider_bookings.filter(status='pending').count()
            completed_bookings = provider_bookings.filter(status='completed').count()
            
            # Calculate rating
            reviews = Review.objects.filter(booking__service_provider=provider)
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0.0
            
            # Today's schedule
            today_schedule = provider_bookings.filter(
                booking_date=today,
                status__in=['pending', 'confirmed']
            ).order_by('booking_time')
            
        except ServiceProvider.DoesNotExist:
            provider = None
            total_bookings = 0
            today_bookings = 0
            pending_bookings = 0
            completed_bookings = 0
            avg_rating = 0.0
            today_schedule = []
            messages.info(request, 'Please complete provider registration')
        
        return render(request, 'provider_dashboard.html', {
            'provider': provider,
            'total_bookings': total_bookings,
            'today_bookings': today_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'avg_rating': avg_rating,
            'today_schedule': today_schedule,
        })
    
    elif user.user_type == 'admin':
        # Admin stats
        total_users = User.objects.count()
        total_customers = User.objects.filter(user_type='customer').count()
        total_providers = User.objects.filter(user_type='service_provider').count()
        total_bookings = Booking.objects.count()
        
        # Revenue calculation
        completed_bookings = Booking.objects.filter(status='completed')
        total_revenue = sum(booking.total_amount for booking in completed_bookings)
        
        # Pending bookings
        pending_bookings = Booking.objects.filter(status='pending').count()
        
        # Recent bookings
        recent_bookings = Booking.objects.all().order_by('-created_at')[:10]
        
        return render(request, 'admin_dashboard.html', {
            'total_users': total_users,
            'total_customers': total_customers,
            'total_providers': total_providers,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'pending_bookings': pending_bookings,
            'recent_bookings': recent_bookings,
        })
    
    # Default fallback - should not reach here with valid user_type
    return render(request, 'dashboard.html')

def register(request):
    """User registration with custom User model"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            
            # Redirect based on user type
            if user.user_type == 'service_provider':
                return redirect('provider_registration')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def book_service(request):
    if request.method == 'POST':
        try:
            service_id = request.POST.get('service_id')
            service = get_object_or_404(Service, id=service_id)

            provider = ServiceProvider.objects.filter(services=service).first()
            if not provider:
                messages.error(request, 'No available provider for this service')
                return redirect('book_service')

            Booking.objects.create(
                customer=request.user,
                service=service,
                service_provider=provider,
                booking_date=request.POST.get('booking_date'),
                booking_time=request.POST.get('booking_time'),
                vehicle_type=request.POST.get('vehicle_type'),
                vehicle_number=request.POST.get('vehicle_number'),
                special_instructions=request.POST.get('special_instructions', ''),
                total_amount=service.price,
                status='pending'
            )

            messages.success(request, 'Booking created successfully!')
            return redirect('my_bookings')

        except Exception as e:
            messages.error(request, str(e))
            return redirect('book_service')

    # GET request
    services = Service.objects.all()
    today = date.today()

    return render(request, 'booking/book_service.html', {
        'services': services,
        'today': today
    })


@login_required
def my_bookings(request):
    """View user's bookings"""
    user = request.user
    
    try:
        if user.user_type == 'customer':
            bookings = Booking.objects.filter(customer=user).order_by('-booking_date', '-booking_time')
        elif user.user_type == 'service_provider':
            try:
                provider = ServiceProvider.objects.get(user=user)
                bookings = Booking.objects.filter(service_provider=provider).order_by('-booking_date', '-booking_time')
            except ServiceProvider.DoesNotExist:
                bookings = []
                messages.error(request, 'Please complete provider registration first')
        else:
            # Admin can see all bookings
            bookings = Booking.objects.all().order_by('-booking_date', '-booking_time')
        
        # Add custom attributes for template
        for booking in bookings:
            # Status colors and icons
            if booking.status == 'completed':
                booking.status_color = 'success'
                booking.status_icon = 'check-circle'
            elif booking.status == 'pending':
                booking.status_color = 'warning'
                booking.status_icon = 'clock'
            elif booking.status == 'confirmed':
                booking.status_color = 'info'
                booking.status_icon = 'check'
            elif booking.status == 'in_progress':
                booking.status_color = 'primary'
                booking.status_icon = 'spinner'
            elif booking.status == 'cancelled':
                booking.status_color = 'danger'
                booking.status_icon = 'times-circle'
            else:
                booking.status_color = 'secondary'
                booking.status_icon = 'question-circle'
            
            # Check if review exists
            try:
                booking.review = Review.objects.get(booking=booking)
            except Review.DoesNotExist:
                booking.review = None
                
    except Exception as e:
        bookings = []
        messages.error(request, f'Error loading bookings: {str(e)}')
    
    return render(request, 'my_bookings.html', {'bookings': bookings})

@login_required
def services_list(request):
    """List services with categories"""
    try:
        services = Service.objects.select_related('category').all()
        categories = ServiceCategory.objects.all()
    except:
        services = []
        categories = []
    
    return render(request, 'services.html', {
        'services': services,
        'categories': categories
    })

@login_required
def profile(request):
    """User profile management"""
    user = request.user
    
    if request.method == 'POST':
        # Update basic user info
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'profile.html', {'user': user})

@login_required
def provider_registration(request):
    """Complete provider registration"""
    if request.user.user_type != 'service_provider':
        messages.error(request, 'This page is only for service providers')
        return redirect('dashboard')
    
    try:
        provider = ServiceProvider.objects.get(user=request.user)
        # Provider already exists, redirect to dashboard
        messages.info(request, 'Provider registration already completed')
        return redirect('dashboard')
    except ServiceProvider.DoesNotExist:
        provider = None
    
    if request.method == 'POST':
        try:
            provider = ServiceProvider.objects.create(
                user=request.user,
                company_name=request.POST.get('company_name'),
                address=request.POST.get('address'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email', request.user.email)
            )
            
            # Add selected services
            service_ids = request.POST.getlist('services')
            services = Service.objects.filter(id__in=service_ids)
            provider.services.set(services)
            
            messages.success(request, 'Provider registration completed!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Registration error: {str(e)}')
    
    # GET request - show registration form
    try:
        services = Service.objects.all()
    except:
        services = []
    
    return render(request, 'registration/provider_registration.html', {
        'services': services
    })

@login_required
def update_booking_status(request, booking_id):
    """Update booking status (for providers)"""
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Only service providers can update booking status')
        return redirect('dashboard')
    
    try:
        provider = ServiceProvider.objects.get(user=request.user)
        booking = get_object_or_404(Booking, id=booking_id, service_provider=provider)
        
        if request.method == 'POST':
            new_status = request.POST.get('status')
            if new_status in dict(Booking.STATUS_CHOICES):
                booking.status = new_status
                booking.save()
                messages.success(request, f'Booking status updated to {booking.get_status_display()}')
            else:
                messages.error(request, 'Invalid status')
        
        return redirect('dashboard')
        
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'Please complete provider registration first')
        return redirect('provider_registration')

@login_required
def add_review(request, booking_id):
    """Add review for completed booking"""
    try:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user, status='completed')
        
        if request.method == 'POST':
            rating = request.POST.get('rating')
            comment = request.POST.get('comment', '')
            
            # Create or update review
            review, created = Review.objects.update_or_create(
                booking=booking,
                defaults={
                    'customer': request.user,
                    'rating': rating,
                    'comment': comment
                }
            )
            
            # Update provider rating
            provider = booking.service_provider
            provider_reviews = Review.objects.filter(booking__service_provider=provider)
            avg_rating = provider_reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0.0
            provider.rating = avg_rating
            provider.save()
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('my_bookings')
        
        return render(request, 'booking/review.html', {'booking': booking})
        
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found or not eligible for review')
        return redirect('my_bookings')

# Simple views for missing pages
def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def faq(request):
    return render(request, 'faq.html')

# Additional utility views
@login_required
def booking_details(request, booking_id):
    """View booking details"""
    try:
        if request.user.user_type == 'customer':
            booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        elif request.user.user_type == 'service_provider':
            provider = get_object_or_404(ServiceProvider, user=request.user)
            booking = get_object_or_404(Booking, id=booking_id, service_provider=provider)
        elif request.user.user_type == 'admin':
            booking = get_object_or_404(Booking, id=booking_id)
        else:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        
        return render(request, 'booking/details.html', {'booking': booking})
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('dashboard')

@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    try:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        
        if booking.status in ['pending', 'confirmed']:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Booking cancelled successfully')
        else:
            messages.error(request, 'Cannot cancel booking in current status')
        
        return redirect('my_bookings')
        
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found')
        return redirect('my_bookings')