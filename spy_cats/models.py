from django.db import models
from django.core.exceptions import ValidationError


class SpyCat(models.Model):
    name = models.CharField(max_length=255)
    years_of_experience = models.IntegerField()
    breed = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.breed}"

    class Meta:
        db_table = 'spy_cats'


class Mission(models.Model):
    cat = models.ForeignKey(
        SpyCat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missions'
    )
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mission {self.id} - {'Complete' if self.complete else 'Incomplete'}"

    def clean(self):
        # Check that mission has between 1-3 targets
        if self.pk:
            target_count = self.targets.count()
            if target_count < 1 or target_count > 3:
                raise ValidationError("Mission must have between 1 and 3 targets")

    def save(self, *args, **kwargs):
        # Auto-complete mission if all targets are complete
        if self.pk:
            all_complete = all(target.complete for target in self.targets.all())
            if all_complete and self.targets.exists():
                self.complete = True
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'missions'


class Target(models.Model):
    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name='targets'
    )
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.country})"

    class Meta:
        db_table = 'targets'
