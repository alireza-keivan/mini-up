# apps/consulting/serializers.py

from rest_framework import serializers
from .models import (
    ConsultingCategory,
    Consultant,
    TimeSlot,
    Appointment,
    ConsultantReview
)


class CategorySerializer(serializers.ModelSerializer):
    """سریالایزر دسته‌بندی"""
    
    class Meta:
        model = ConsultingCategory
        fields = ['id', 'name', 'slug', 'icon', 'description']


class ConsultantListSerializer(serializers.ModelSerializer):
    """لیست مشاوران - خلاصه"""
    
    name = serializers.CharField(source='display_name', read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Consultant
        fields = [
            'id', 'name', 'title', 'profile_image',
            'price_per_minute', 'rating', 'review_count',
            'experience_years', 'is_online', 'categories'
        ]


class ConsultantDetailSerializer(serializers.ModelSerializer):
    """جزئیات مشاور"""
    
    name = serializers.CharField(source='display_name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Consultant
        fields = [
            'id', 'name', 'phone', 'title', 'bio',
            'profile_image', 'cover_image',
            'price_per_minute', 'session_price_15', 'session_price_30', 'session_price_60',
            'min_session_duration', 'max_session_duration',
            'experience_years', 'education', 'certifications',
            'rating', 'review_count', 'total_sessions',
            'is_online', 'is_available', 'categories'
        ]


class TimeSlotSerializer(serializers.ModelSerializer):
    """بازه زمانی"""
    
    price = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = [
            'id', 'date', 'start_time', 'end_time',
            'duration', 'status', 'price', 'is_available'
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    """نوبت مشاوره"""
    
    consultant_name = serializers.CharField(source='consultant.display_name', read_only=True)
    slot_info = TimeSlotSerializer(source='slot', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'consultant', 'consultant_name',
            'slot', 'slot_info', 'price', 'status',
            'description', 'session_link',
            'created_at', 'started_at', 'finished_at'
        ]
        read_only_fields = ['id', 'price', 'status', 'session_link', 'created_at']


class BookAppointmentSerializer(serializers.Serializer):
    """رزرو نوبت"""
    
    slot_id = serializers.UUIDField()
    description = serializers.CharField(max_length=300, required=False, allow_blank=True)


class ReviewSerializer(serializers.ModelSerializer):
    """نظر کاربر"""
    
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultantReview
        fields = ['id', 'rating', 'comment', 'user_name', 'created_at']
    
    def get_user_name(self, obj):
        name = obj.user.get_full_name()
        if name:
            # فقط حرف اول نام خانوادگی
            parts = name.split()
            if len(parts) > 1:
                return f"{parts[0]} {parts[1][0]}."
            return parts[0]
        return "کاربر"


class CreateReviewSerializer(serializers.Serializer):
    """ثبت نظر"""
    
    appointment_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)
