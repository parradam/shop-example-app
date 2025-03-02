import redis
from django.conf import settings
from requests import delete
from .models import Product

# Connect to Redis
r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)

class Recommender:
    def get_product_key(self, id):
        return f'product:{id}:purchased_with'
    
    def products_bought(self, products):
        product_ids = [p.id for p in products]
        for product_id in product_ids:
            for with_id in product_ids:
                # Get the other products bought with each product
                if product_id != with_id:
                    # Increment score for products bought together
                    r.zincrby(
                        self.get_product_key(product_id),
                        1,
                        with_id
                    )
    
    def suggest_products_for(self, products, max_results=6):
        product_ids = [p.id for p in products]
        if len(products) == 1:
            # One product
            suggestions = r.zrange(
                self.get_product_key(product_ids[0]),
                0,
                -1,
                desc=True
            )[:max_results]
        else:
            # Multiple products
            # Generate temp key
            flat_ids = ''.join([str(id) for id in product_ids])
            temp_key = f'tmp_{flat_ids}'
            # Combine scores of all products, store sorted set in temp key
            keys = [self.get_product_key(id) for id in product_ids]
            r.zunionstore(temp_key, keys)
            # Remove IDs for product the recommendation is for
            r.zrem(temp_key, *product_ids)
            # Get product IDs by score, sort descending
            suggestions = r.zrange(
                temp_key,
                0,
                -1,
                desc=True
            )[:max_results]
            # Remove temp key
            r.delete(temp_key)
        suggested_products_ids = [int(id) for id in suggestions]
        # Get suggested products and sort by order of appearance
        suggested_products = list(
            Product.objects.filter(id__in=suggested_products_ids)
        )
        suggested_products.sort(
            key=lambda x: suggested_products_ids.index(x.id)
        )
        return suggested_products
    
    def clear_purchases(self):
        for id in Product.objects.values_list('id', flat=True):
            r.delete(self.get_product_key(id))