# apps/consulting/api_views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import ConsultingCategory, Consultant, Appointment
from .services import ConsultingService
from .serializers import (
    CategorySerializer,
    ConsultantListSerializer,
    ConsultantDetailSerializer,
    TimeSlotSerializer,
    AppointmentSerializer,
    BookAppointmentSerializer,
    ReviewSerializer,
    CreateReviewSerializer
)


class CategoryListAPI(APIView):
    """لیست دسته‌بندی‌ها"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        categories = ConsultingCategory.objects.filter(is_active=True)
        data = CategorySerializer(categories, many=True).data
        return Response(data)
    
class ConsultantListAPI(APIView):
    """لیست مشاوران"""
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.GET.get('category')
        consultants = ConsultingService.get_active_consultants(category_slug=category)
        data = ConsultantListSerializer(consultants, many=True).data
        return Response(data)


class ConsultantDetailAPI(APIView):
    """جزئیات مشاور"""
    permission_classes = [AllowAny]

    def get(self, request, consultant_id):
        consultant = ConsultingService.get_consultant(consultant_id)
        if not consultant:
            return Response({'error': 'مشاور یافت نشد'}, status=404)
        data = ConsultantDetailSerializer(consultant).data
        return Response(data)


class ConsultantSlotsAPI(APIView):
    """اسلات‌های مشاور"""
    permission_classes = [AllowAny]

    def get(self, request, consultant_id):
        date = request.GET.get('date')
        slots = ConsultingService.get_available_slots(consultant_id, date)
        data = TimeSlotSerializer(slots, many=True).data
        return Response(data)


class BookAppointmentAPI(APIView):
    """رزرو نوبت"""
    permission_classes = [IsAuthenticated]

    def post(self, request, consultant_id):
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        slot_id = serializer.validated_data['slot_id']
        description = serializer.validated_data.get('description', '')

        result = ConsultingService.book_appointment(
            user=request.user,
            slot_id=slot_id,
            description=description
        )

        if not result['success']:
            return Response(result, status=400)

        return Response(AppointmentSerializer(result['appointment']).data)


class AppointmentDetailAPI(APIView):
    """جزئیات نوبت"""
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(id=appointment_id, user=request.user)
        except Appointment.DoesNotExist:
            return Response({'error': 'نوبت یافت نشد'}, status=404)

        return Response(AppointmentSerializer(appointment).data)


class SubmitReviewAPI(APIView):
    """ثبت نظر"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = ConsultingService.add_review(
            user=request.user,
            appointment_id=serializer.validated_data['appointment_id'],
            rating=serializer.validated_data['rating'],
            comment=serializer.validated_data.get('comment', '')
        )

        if not result['success']:
            return Response(result, status=400)

        return Response(ReviewSerializer(result['review']).data, status=201)


class ConsultantReviewsAPI(APIView):
    """نمایش نظرات مشاور"""
    permission_classes = [AllowAny]

    def get(self, request, consultant_id):
        reviews = ConsultingService.get_consultant_reviews(consultant_id)
        return Response(ReviewSerializer(reviews, many=True).data)