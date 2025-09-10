# apps/analytics/repositories/query_builder.py
class SQLQueryBuilder:
    def __init__(self):
        self.base_query = ""
        self.filters = []
        self.params = []
    
    def add_tenant_filter(self, tenant_id: int):
        self.filters.append("tenant_id = %s")
        self.params.append(tenant_id)
        return self
    
    def add_date_range(self, start_date, end_date):
        self.filters.append("timestamp BETWEEN %s AND %s")
        self.params.extend([start_date, end_date])
        return self
    
    def build(self) -> tuple:
        where_clause = " AND ".join(self.filters) if self.filters else "1=1"
        final_query = f"{self.base_query} WHERE {where_clause}"
        return final_query, self.params