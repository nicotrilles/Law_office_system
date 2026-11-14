"""Reusable abstract models shared by the other apps."""
from django.db import models


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at, matching the columns used across the logical schema."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
