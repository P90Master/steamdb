from mongoengine.signals import post_save, post_delete
from django.core.cache import cache


def get_game_document():
    from games.documents import Game
    return Game


def invalidate_cache_on_save(sender, document, **kwargs):
    cache_key = f'game_detail_{document.id}'
    cache.delete(cache_key)


def invalidate_cache_on_delete(sender, document, **kwargs):
    cache_key = f'game_detail_{document.id}'
    cache.delete(cache_key)


post_save.connect(invalidate_cache_on_save, sender=get_game_document())
post_delete.connect(invalidate_cache_on_delete, sender=get_game_document())
