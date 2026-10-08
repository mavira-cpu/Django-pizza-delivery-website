from django.db import models
from django.urls import reverse
# Create your models here.
from django.contrib.auth.models import User
import uuid


class Category(models.Model):
    """Pizza category (e.g., Pizzas, Sides, Drinks)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, null=True,help_text="Emoji or icon")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class MenuItem(models.Model):

    """Individual menu item"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(default='fallback.png', upload_to='menu/', blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('shop:item_detail', kwargs={'slug': self.slug})
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('cash', 'Cash on Delivery'),
        ('card', 'Card Payment'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    
    items = models.JSONField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, default='pending')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # NEW: Track status history
    status_history = models.JSONField(default=list, blank=True)
    
    special_instructions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"PIZ-{uuid.uuid4().hex[:8].upper()}"
        
        # Track status changes
        if self.pk:
            old_status = Order.objects.get(pk=self.pk).status
            if old_status != self.status:
                # Add to history
                history = self.status_history or []
                history.append({
                    'old_status': old_status,
                    'new_status': self.status,
                    'timestamp': self.updated_at.isoformat() if self.updated_at else None
                })
                self.status_history = history
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    class Meta:
        ordering = ['-created_at']