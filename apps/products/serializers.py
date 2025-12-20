# apps/products/serializers.py

from rest_framework import serializers
from django.db.models import Avg, Count
from .models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    DigitalInventory, GameCurrencyRate, ProductReview,
    ProductFAQ, Wishlist, RecentlyViewed
)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class CategoryMinimalSerializer(serializers.ModelSerializer):
    """Minimal category data for nested representations."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']


class CategorySerializer(serializers.ModelSerializer):
    """Standard category serializer."""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'name_en', 'slug',
            'description', 'image', 'icon', 'is_active', 'is_featured',
            'sort_order', 'products_count'
        ]
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Category with nested children for tree structure."""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'image', 'children']
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('sort_order')
        return CategoryTreeSerializer(children, many=True).data


# ═══════════════════════════════════════════════════════════════════════════════
# BRAND SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class BrandSerializer(serializers.ModelSerializer):
    """Brand serializer."""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'name_en', 'slug', 'logo',
            'description', 'website', 'is_active', 'products_count'
        ]
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class BrandMinimalSerializer(serializers.ModelSerializer):
    """Minimal brand data."""
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo']


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT IMAGE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer."""
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'sort_order']


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT VARIANT SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ProductVariantSerializer(serializers.ModelSerializer):
    """Product variant serializer."""
    
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'attributes', 'price', 'original_price',
            'stock', 'is_active', 'sort_order', 'discount_percentage', 'is_in_stock'
        ]
    
    def get_is_in_stock(self, obj):
        # For digital products, check digital inventory
        if obj.product.is_digital:
            return DigitalInventory.get_available_count(obj.product, obj) > 0
        return obj.stock > 0


# ═══════════════════════════════════════════════════════════════════════════════
# GAME CURRENCY RATE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class GameCurrencyRateSerializer(serializers.ModelSerializer):
    """Game currency rate serializer."""
    
    class Meta:
        model = GameCurrencyRate
        fields = [
            'id', 'min_amount', 'max_amount', 'price_per_unit',
            'unit_name', 'is_active'
        ]


class GameCurrencyCalculateSerializer(serializers.Serializer):
    """Serializer for calculating game currency price."""
    
    product_id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)
    
    def validate(self, data):
        try:
            product = Product.objects.get(
                pk=data['product_id'],
                product_type=Product.ProductType.GAME_CURRENCY,
                is_active=True
            )
            data['product'] = product
        except Product.DoesNotExist:
            raise serializers.ValidationError({'product_id': 'محصول یافت نشد یا ارز بازی نیست'})
        
        rate = GameCurrencyRate.get_rate_for_amount(product, data['amount'])
        if not rate:
            raise serializers.ValidationError({'amount': 'نرخی برای این مقدار تعریف نشده است'})
        
        data['rate'] = rate
        return data


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT REVIEW SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ProductReviewSerializer(serializers.ModelSerializer):
    """Product review serializer."""
    
    user_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'user_display', 'rating', 'title', 'comment',
            'is_verified_purchase', 'admin_response', 'responded_at',
            'created_at'
        ]
        read_only_fields = ['user_display', 'is_verified_purchase', 'admin_response', 'responded_at']
    
    def get_user_display(self, obj):
        """Return masked user name for privacy."""
        if obj.user.first_name:
            name = obj.user.first_name
            if len(name) > 2:
                return f"{name[0]}***{name[-1]}"
            return f"{name[0]}***"
        # Mask phone number
        phone = obj.user.phone
        return f"{phone[:4]}***{phone[-2:]}"


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""
    
    class Meta:
        model = ProductReview
        fields = ['product', 'rating', 'title', 'comment']
    
    def validate(self, data):
        user = self.context['request'].user
        product = data['product']
        
        # Check if user already reviewed this product
        if ProductReview.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError('شما قبلاً برای این محصول نظر ثبت کرده‌اید')
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Check if user has purchased this product
        from apps.orders.models import Order, OrderItem
        has_purchased = OrderItem.objects.filter(
            order__user=user,
            order__status=Order.Status.COMPLETED,
            product=validated_data['product']
        ).exists()
        validated_data['is_verified_purchase'] = has_purchased
        
        return super().create(validated_data)


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT FAQ SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ProductFAQSerializer(serializers.ModelSerializer):
    """Product FAQ serializer."""
    
    class Meta:
        model = ProductFAQ
        fields = ['id', 'question', 'answer', 'sort_order']


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list views (minimal data)."""
    
    category = CategoryMinimalSerializer(read_only=True)
    brand = BrandMinimalSerializer(read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'uuid', 'sku', 'name', 'slug', 'category', 'brand',
            'product_type', 'delivery_type', 'short_description',
            'price', 'original_price', 'discount_percentage',
            'main_image', 'is_in_stock', 'is_featured', 'is_new',
            'is_bestseller', 'average_rating', 'review_count'
        ]
    
    def get_average_rating(self, obj):
        result = obj.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full product detail serializer."""
    
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True, source='variants.filter(is_active=True)')
    faqs = ProductFAQSerializer(many=True, read_only=True, source='faqs.filter(is_active=True)')
    currency_rates = GameCurrencyRateSerializer(many=True, read_only=True, source='currency_rates.filter(is_active=True)')
    
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_digital = serializers.ReadOnlyField()
    requires_shipping = serializers.ReadOnlyField()
    
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()
    
    is_wishlisted = serializers.SerializerMethodField()
    digital_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'uuid', 'sku', 'name', 'name_en', 'slug',
            'category', 'brand', 'product_type', 'delivery_type',
            'short_description', 'description', 'specifications',
            'price', 'original_price', 'discount_percentage',
            'stock', 'is_in_stock', 'is_low_stock',
            'weight', 'dimensions',
            'main_image', 'images',
            'meta_title', 'meta_description',
            'is_active', 'is_featured', 'is_new', 'is_bestseller',
            'is_digital', 'requires_shipping',
            'view_count', 'sales_count',
            'variants', 'faqs', 'currency_rates',
            'average_rating', 'review_count', 'rating_distribution',
            'is_wishlisted', 'digital_stock',
            'created_at', 'updated_at'
        ]
    
    def get_variants(self, obj):
        variants = obj.variants.filter(is_active=True).order_by('sort_order')
        return ProductVariantSerializer(variants, many=True).data
    
    def get_faqs(self, obj):
        faqs = obj.faqs.filter(is_active=True).order_by('sort_order')
        return ProductFAQSerializer(faqs, many=True).data
    
    def get_currency_rates(self, obj):
        if obj.product_type != Product.ProductType.GAME_CURRENCY:
            return []
        rates = obj.currency_rates.filter(is_active=True).order_by('min_amount')
        return GameCurrencyRateSerializer(rates, many=True).data
    
    def get_average_rating(self, obj):
        result = obj.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_rating_distribution(self, obj):
        """Get count of reviews for each rating (1-5)."""
        reviews = obj.reviews.filter(is_approved=True)
        distribution = {}
        for i in range(1, 6):
            distribution[str(i)] = reviews.filter(rating=i).count()
        return distribution
    
    def get_is_wishlisted(self, obj):
        """Check if current user has wishlisted this product."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, product=obj).exists()
        return False
    
    def get_digital_stock(self, obj):
        """Get available digital inventory count for digital products."""
        if not obj.is_digital:
            return None
        return DigitalInventory.get_available_count(obj)


class ProductSearchSerializer(serializers.ModelSerializer):
    """Lightweight serializer for search results."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'main_image', 'price',
            'original_price', 'category_name', 'product_type'
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# WISHLIST SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class WishlistSerializer(serializers.ModelSerializer):
    """Wishlist serializer with product details."""
    
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['created_at']


class WishlistCreateSerializer(serializers.Serializer):
    """Serializer for adding product to wishlist."""
    
    product_id = serializers.IntegerField()
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError('محصول یافت نشد')
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        product_id = validated_data['product_id']
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=user,
            product_id=product_id
        )
        return wishlist_item


# ═══════════════════════════════════════════════════════════════════════════════
# RECENTLY VIEWED SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class RecentlyViewedSerializer(serializers.ModelSerializer):
    """Recently viewed products serializer."""
    
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = RecentlyViewed
        fields = ['id', 'product', 'viewed_at']


# ═══════════════════════════════════════════════════════════════════════════════
# DIGITAL INVENTORY SERIALIZERS (Admin use)
# ═══════════════════════════════════════════════════════════════════════════════

class DigitalInventorySerializer(serializers.ModelSerializer):
    """Digital inventory serializer (for admin)."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DigitalInventory
        fields = [
            'id', 'product', 'product_name', 'variant', 'variant_name',
            'credential_type', 'credential_data', 'status', 'status_display',
            'sold_at', 'created_at'
        ]
        read_only_fields = ['status', 'sold_at', 'sold_to', 'order_item']


class DigitalInventoryBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating digital inventory items."""
    
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    credential_type = serializers.ChoiceField(choices=DigitalInventory.CredentialType.choices)
    credentials = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=1000,
        help_text='لیست اطلاعات حساب‌ها [{"username": "...", "password": "..."}, ...]'
    )
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value, is_digital=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError('محصول دیجیتال یافت نشد')
        return value
    
    def validate_variant_id(self, value):
        if value:
            try:
                ProductVariant.objects.get(pk=value)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError('واریانت یافت نشد')
        return value
    
    def create(self, validated_data):
        product_id = validated_data['product_id']
        variant_id = validated_data.get('variant_id')
        credential_type = validated_data['credential_type']
        credentials = validated_data['credentials']
        
        created_items = []
        for cred_data in credentials:
            item = DigitalInventory.objects.create(
                product_id=product_id,
                variant_id=variant_id,
                credential_type=credential_type,
                credential_data=cred_data,
                status=DigitalInventory.Status.AVAILABLE
            )
            created_items.append(item)
        
        return created_items


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARISON SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ProductCompareSerializer(serializers.ModelSerializer):
    """Serializer for product comparison view."""
    
    category = CategoryMinimalSerializer(read_only=True)
    brand = BrandMinimalSerializer(read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'brand',
            'main_image', 'price', 'original_price', 'discount_percentage',
            'specifications', 'stock', 'average_rating', 'review_count',
            'is_in_stock', 'product_type'
        ]
    
    def get_average_rating(self, obj):
        result = obj.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()


# ═══════════════════════════════════════════════════════════════════════════════
# MISSING SERIALIZERS (اضافه شده)
# ═══════════════════════════════════════════════════════════════════════════════

class CategoryDetailSerializer(serializers.ModelSerializer):
    """Category detail with full information."""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'name_en', 'slug',
            'description', 'image', 'icon',
            'is_active', 'is_featured', 'sort_order',
            'products_count',
            'meta_title', 'meta_description'
        ]
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class BrandDetailSerializer(serializers.ModelSerializer):
    """Brand detail with full information."""
    
    products_count = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'name_en', 'slug', 'logo',
            'description', 'website', 'is_active',
            'products_count', 'categories',
            'meta_title', 'meta_description'
        ]
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
    def get_categories(self, obj):
        """Get unique categories that have products from this brand."""
        category_ids = obj.products.filter(is_active=True).values_list('category_id', flat=True).distinct()
        categories = Category.objects.filter(id__in=category_ids, is_active=True)
        return CategoryMinimalSerializer(categories, many=True).data


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products (Admin)."""
    
    class Meta:
        model = Product
        fields = [
            'name', 'name_en', 'slug', 'category', 'brand',
            'product_type', 'delivery_type',
            'short_description', 'description', 'specifications',
            'price', 'original_price', 'stock', 'low_stock_threshold',
            'weight', 'dimensions', 'main_image',
            'meta_title', 'meta_description',
            'is_active', 'is_featured', 'is_new', 'is_bestseller'
        ]
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('قیمت باید بزرگتر از صفر باشد')
        return value
    
    def validate(self, data):
        # اگر original_price داده شده، باید از price بیشتر باشد
        if data.get('original_price') and data.get('price'):
            if data['original_price'] <= data['price']:
                raise serializers.ValidationError({
                    'original_price': 'قیمت اصلی باید از قیمت فروش بیشتر باشد'
                })
        return data


class ProductAdminSerializer(serializers.ModelSerializer):
    """Full product serializer for admin panel."""
    
    category = CategoryMinimalSerializer(read_only=True)
    brand = BrandMinimalSerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    brand_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants_count = serializers.SerializerMethodField()
    digital_inventory_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_variants_count(self, obj):
        return obj.variants.count()
    
    def get_digital_inventory_count(self, obj):
        if obj.is_digital:
            return DigitalInventory.objects.filter(
                product=obj,
                status=DigitalInventory.Status.AVAILABLE
            ).count()
        return None


class DigitalInventoryAdminSerializer(serializers.ModelSerializer):
    """Digital inventory admin serializer with sensitive data."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    credential_type_display = serializers.CharField(source='get_credential_type_display', read_only=True)
    sold_to_phone = serializers.CharField(source='sold_to.phone', read_only=True, allow_null=True)
    
    class Meta:
        model = DigitalInventory
        fields = [
            'id', 'product', 'product_name', 'variant', 'variant_name',
            'credential_type', 'credential_type_display',
            'credential_data', 'status', 'status_display',
            'sold_to', 'sold_to_phone', 'sold_at',
            'order_item', 'admin_note',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['sold_to', 'sold_at', 'order_item']

# ═══════════════════════════════════════════════════════════════════════════════
# MISSING SERIALIZERS (Required by api_views.py)
# Add these at the END of serializers.py
# ═══════════════════════════════════════════════════════════════════════════════

from apps.products.models import (
    Category, Brand, Product, ProductVariant, ProductImage,
    ProductReview, Wishlist, WishlistItem
)

# -------------------------------
# CATEGORY SERIALIZERS
# -------------------------------

class CategoryDetailSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'name_en', 'slug',
            'parent', 'children',
            'description', 'image', 'icon',
            'is_active', 'is_featured',
            'sort_order', 'products_count'
        ]

    def get_parent(self, obj):
        if obj.parent:
            return {
                'id': obj.parent.id,
                'name': obj.parent.name,
                'slug': obj.parent.slug
            }
        return None

    def get_children(self, obj):
        return [
            {
                'id': c.id,
                'name': c.name,
                'slug': c.slug
            }
            for c in obj.children.filter(is_active=True).order_by('sort_order')
        ]

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


# -------------------------------
# BRAND SERIALIZERS
# -------------------------------

class BrandDetailSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'name_en', 'slug',
            'logo', 'description', 'website',
            'is_active', 'products_count'
        ]

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


# -------------------------------
# PRODUCT CARD SERIALIZER (for lists)
# -------------------------------

class ProductCardSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    brand = serializers.CharField(source='brand.name', read_only=True)
    price_after_discount = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'name_en', 'slug',
            'category', 'brand',
            'price', 'original_price',
            'price_after_discount',
            'is_active', 'is_featured', 'is_new',
            'image'
        ]

    def get_image(self, obj):
        main = obj.images.filter(is_main=True).first()
        if main:
            return main.image.url
        img = obj.images.first()
        return img.image.url if img else None

    def get_price_after_discount(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            return obj.price
        return obj.price


# -------------------------------
# WISHLIST SERIALIZERS
# -------------------------------

class WishlistSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ['id', 'items_count']

    def get_items_count(self, obj):
        return obj.items.count()


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductCardSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'created_at']
