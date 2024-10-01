class CompetitorAnalysis:
    def __init__(self, products):
        self.products = products

    def get_competitors(self, product):
        competitors = []
        for other_product in self.products:
            if product.category == other_product.category and product.sku != other_product.sku:
                diff = abs(product.get_score() - other_product.get_score())
                competitors.append((other_product.sku, diff))

        # Sort by score difference and get the closest competitors
        return sorted(competitors, key=lambda x: x[1])[:10]
