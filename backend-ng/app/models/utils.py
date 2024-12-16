from typing import Self

from beanie import Document


class BaseDocument(Document):
    async def pre_save(self):
        pass

    async def post_save(self):
        pass

    async def save(self, *args, **kwargs) -> Self:
        await self.pre_save()
        await super().save(*args, **kwargs)
        await self.post_save()
        return self
