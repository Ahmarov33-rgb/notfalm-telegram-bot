import httpx
from typing import Optional, List, Dict, Any
from config import settings


class APIClient:
    def __init__(self):
        self.base_url = settings.API_URL
        self.headers = {
            "Content-Type": "application/json",
            "x-bot-secret": settings.SECRET_KEY
        }

    def admin_headers(self, admin_id: int) -> dict:
        return {**self.headers, "x-admin-id": str(admin_id)}

    async def upsert_user(self, telegram_id: int, username: str = None,
                          first_name: str = None, last_name: str = None) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/api/users/upsert", json={
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            })
            return r.json()

    async def get_categories(self) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/categories/")
            return r.json()

    async def get_products(self, category_id: int = None) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            params = {}
            if category_id:
                params["category_id"] = category_id
            r = await client.get(f"{self.base_url}/api/products/", params=params)
            return r.json()

    async def get_product(self, product_id: int) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/products/{product_id}")
            if r.status_code == 200:
                return r.json()
            return None

    async def get_orders(self, admin_id: int, status: str = None) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            params = {}
            if status:
                params["status"] = status
            r = await client.get(
                f"{self.base_url}/api/orders/",
                params=params,
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def get_user_orders(self, telegram_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/orders/user/{telegram_id}")
            return r.json()

    async def confirm_order(self, order_id: int, admin_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/orders/{order_id}/confirm",
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def cancel_order(self, order_id: int, admin_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/orders/{order_id}/cancel",
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def get_stats(self, admin_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/api/admin/stats",
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def create_category(self, admin_id: int, name: str, slug: str,
                               emoji: str = "📦") -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/categories/",
                json={"name": name, "slug": slug, "emoji": emoji},
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def delete_category(self, admin_id: int, category_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.delete(
                f"{self.base_url}/api/categories/{category_id}",
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def create_product(self, admin_id: int, data: Dict) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/products/",
                json=data,
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def update_product(self, admin_id: int, product_id: int, data: Dict) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.patch(
                f"{self.base_url}/api/products/{product_id}",
                json=data,
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def delete_product(self, admin_id: int, product_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.delete(
                f"{self.base_url}/api/products/{product_id}",
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def bulk_add_digital_items(self, admin_id: int, product_id: int,
                                      contents: List[str]) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/digital-items/bulk",
                json={"product_id": product_id, "contents": contents},
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def get_stock(self, product_id: int) -> int:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/digital-items/stock/{product_id}")
            return r.json().get("stock", 0)

    async def get_support_tickets(self, admin_id: int) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/api/support/",
                headers=self.admin_headers(admin_id)
            )
            return r.json()

    async def reply_ticket(self, admin_id: int, ticket_id: int, reply: str) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/support/{ticket_id}/reply",
                json={"admin_reply": reply},
                headers=self.admin_headers(admin_id)
            )
            return r.json()


api = APIClient()
