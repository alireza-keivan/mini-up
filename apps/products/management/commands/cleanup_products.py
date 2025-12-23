"""
Django management command to clean up old/orphaned products
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.products.models import Product


class Command(BaseCommand):
    help = 'Clean up old products that are not visible in admin (game_currency type products)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--type',
            type=str,
            default='game_currency',
            help='Product type to delete (default: game_currency)',
        )
        parser.add_argument(
            '--all-old',
            action='store_true',
            help='Delete all products with old product_type values',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        product_type = options['type']
        all_old = options['all_old']

        self.stdout.write(self.style.NOTICE('\n' + '='*70))
        self.stdout.write(self.style.NOTICE('PRODUCT CLEANUP TOOL'))
        self.stdout.write(self.style.NOTICE('='*70 + '\n'))

        # Get all products
        all_products = Product.objects.all()
        self.stdout.write(f'Total products in database: {all_products.count()}\n')

        # Find products to delete
        if all_old:
            # Delete products that don't match current ProductType choices
            valid_types = [choice[0] for choice in Product.ProductType.choices]
            products_to_delete = all_products.exclude(product_type__in=valid_types)
            self.stdout.write(f'Valid product types: {", ".join(valid_types)}')
        else:
            # Delete products of specific type
            products_to_delete = all_products.filter(product_type=product_type)
            self.stdout.write(f'Searching for products with type: {product_type}')

        count = products_to_delete.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No products found to delete!'))
            return

        self.stdout.write(self.style.WARNING(f'\nFound {count} product(s) to delete:\n'))
        self.stdout.write('-' * 70)

        # List products to be deleted
        for product in products_to_delete:
            self.stdout.write(
                f'ID: {product.id:3d} | '
                f'Name: {product.name:30s} | '
                f'Type: {product.product_type:15s} | '
                f'Category: {str(product.category):20s}'
            )

        self.stdout.write('-' * 70)

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n🔍 DRY RUN MODE - No changes made'))
            self.stdout.write(self.style.NOTICE(f'   {count} product(s) would be deleted'))
            self.stdout.write(self.style.NOTICE('\nTo actually delete, run without --dry-run flag'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️  About to delete {count} product(s)!'))
            confirm = input('\nType "yes" to confirm deletion: ')

            if confirm.lower() == 'yes':
                with transaction.atomic():
                    # Get related data counts before deletion
                    image_count = sum(p.images.count() for p in products_to_delete)
                    
                    # Delete products
                    deleted_count, deleted_details = products_to_delete.delete()
                    
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully deleted {count} product(s)'))
                    
                    if image_count > 0:
                        self.stdout.write(self.style.SUCCESS(f'✓ Also deleted {image_count} related image(s)'))
                    
                    # Show detailed deletion info
                    self.stdout.write('\nDetailed deletion summary:')
                    for model, count in deleted_details.items():
                        self.stdout.write(f'  - {model}: {count}')
            else:
                self.stdout.write(self.style.ERROR('\n✗ Deletion cancelled'))

        self.stdout.write(self.style.NOTICE('\n' + '='*70 + '\n'))
