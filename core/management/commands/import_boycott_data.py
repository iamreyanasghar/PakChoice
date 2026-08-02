import csv
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import SubCategory, Product, Alternative


class Command(BaseCommand):
    help = 'Import boycott products and their Pakistani alternatives from CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing boycott product data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually saving to the database'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY RUN MODE - No data will be saved"))

        self.stdout.write(self.style.SUCCESS(f"📂 Reading CSV file: {csv_file_path}"))

        # Statistics counters
        stats = {
            'products_created': 0,
            'products_updated': 0,
            'alternatives_created': 0,
            'alternatives_updated': 0,
            'skipped': 0,
            'errors': 0,
        }

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                self.stdout.write(f"📊 Found {len(rows)} rows in CSV")

                with transaction.atomic():
                    for row_num, row in enumerate(rows, start=2):
                        self.stdout.write(f"\n{'='*60}")
                        self.stdout.write(f"Processing row {row_num - 1}")

                        # Get fields from CSV
                        subcategory_slug = row.get('subcategory_slug', '').strip()
                        product_name = row.get('product_name', '').strip()
                        product_slug = row.get('product_slug', '').strip()
                        product_brand = row.get('product_brand', '').strip()
                        country_of_origin = row.get('country_of_origin', '').strip()
                        reason = row.get('reason', '').strip()
                        alternatives_json = row.get('alternatives_json', '').strip()

                        # Validate required fields
                        if not all([subcategory_slug, product_name, product_slug, product_brand, reason]):
                            self.stdout.write(self.style.ERROR(f"❌ Row {row_num - 1}: Missing required fields"))
                            stats['skipped'] += 1
                            continue

                        # Get subcategory
                        try:
                            subcategory = SubCategory.objects.get(slug=subcategory_slug)
                        except SubCategory.DoesNotExist:
                            self.stdout.write(self.style.ERROR(f"❌ Row {row_num - 1}: SubCategory '{subcategory_slug}' not found"))
                            stats['skipped'] += 1
                            continue

                        self.stdout.write(f"📌 Subcategory: {subcategory.name} ({subcategory_slug})")
                        self.stdout.write(f"📌 Product: {product_name} (Brand: {product_brand})")

                        # Create or update Product
                        if not dry_run:
                            product, created = Product.objects.update_or_create(
                                slug=product_slug,
                                defaults={
                                    'subcategory': subcategory,
                                    'name': product_name,
                                    'brand': product_brand,
                                    'country_of_origin': country_of_origin,
                                    'reason': reason,
                                    'image_url': row.get('image_url', '').strip(),
                                    'logo_url': row.get('logo_url', '').strip(),
                                    'verified': True,
                                    'is_active': True,
                                }
                            )

                            if created:
                                stats['products_created'] += 1
                                self.stdout.write(self.style.SUCCESS(f"✅ Created product: {product.name}"))
                            else:
                                stats['products_updated'] += 1
                                self.stdout.write(self.style.SUCCESS(f"🔄 Updated product: {product.name}"))

                            # Process alternatives
                            if alternatives_json:
                                try:
                                    alternatives_data = json.loads(alternatives_json)
                                    self.stdout.write(f"📌 Found {len(alternatives_data)} alternative(s)")

                                    for alt_idx, alt_data in enumerate(alternatives_data, 1):
                                        alt_name = alt_data.get('name', '').strip()
                                        alt_brand = alt_data.get('brand', '').strip()
                                        alt_description = alt_data.get('description', '').strip()
                                        alt_website = alt_data.get('website', '').strip()

                                        if not alt_name:
                                            self.stdout.write(self.style.WARNING(f"⚠️ Alternative {alt_idx}: No name provided, skipping"))
                                            continue

                                        # Create or update Alternative
                                        alternative, alt_created = Alternative.objects.update_or_create(
                                            product=product,
                                            name=alt_name,
                                            defaults={
                                                'brand': alt_brand,
                                                'description': alt_description,
                                                'website': alt_website,
                                                'status': 'approved',
                                                'is_active': True,
                                            }
                                        )

                                        if alt_created:
                                            stats['alternatives_created'] += 1
                                            self.stdout.write(self.style.SUCCESS(f"  ✅ Created alternative: {alt_name}"))
                                        else:
                                            stats['alternatives_updated'] += 1
                                            self.stdout.write(self.style.SUCCESS(f"  🔄 Updated alternative: {alt_name}"))

                                except json.JSONDecodeError as e:
                                    self.stdout.write(self.style.ERROR(f"❌ JSON parse error for alternatives: {e}"))
                                    stats['errors'] += 1

                        else:  # Dry run mode
                            self.stdout.write(self.style.WARNING(f"   [DRY RUN] Would create/update product: {product_name}"))

                            if alternatives_json:
                                try:
                                    alternatives_data = json.loads(alternatives_json)
                                    for alt in alternatives_data:
                                        self.stdout.write(self.style.WARNING(f"   [DRY RUN] Would create alternative: {alt.get('name', 'Unknown')}"))
                                except:
                                    pass

                if dry_run:
                    # In dry run, we need to explicitly rollback since atomic() will commit at the end
                    self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN COMPLETE - No data was saved"))
                else:
                    self.stdout.write(self.style.SUCCESS("\n✅ All data saved successfully!"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"❌ File not found: {csv_file_path}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ An error occurred: {str(e)}"))
            stats['errors'] += 1

        # Print summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 IMPORT SUMMARY")
        self.stdout.write("=" * 60)
        self.stdout.write(f"✅ Products created: {stats['products_created']}")
        self.stdout.write(f"🔄 Products updated: {stats['products_updated']}")
        self.stdout.write(f"✅ Alternatives created: {stats['alternatives_created']}")
        self.stdout.write(f"🔄 Alternatives updated: {stats['alternatives_updated']}")
        self.stdout.write(f"⏭️ Skipped: {stats['skipped']}")
        self.stdout.write(f"❌ Errors: {stats['errors']}")
        self.stdout.write("=" * 60)
