from django.db import models

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        abstract = True
        ordering = ['order']

    def save(self, *args, **kwargs):
        cls = self.__class__
        max = cls.objects.all().aggregate(m=models.Max('order'))['m'] or 0
        if self.order > max + 1 or not self.order:
            self.order = max + 1
        super(OrderedModel, self).save(*args, **kwargs)

    def move(self, to):
        cls = self.__class__

        if not self.pk: raise Exception('save before moving')

        if to < 1: raise ValueError('to must be positive')
        max = cls.objects.all().aggregate(m=models.Max('order'))['m'] or 1
        if to > max: to = max
        if to == self.order: return

        if to < self.order:
            models.objects.filter(order__gte=to, order__lt=self.order) \
                          .update(order=models.F('order') + 1)
        else:
            models.objects.filter(order__lte=to, order__gt=self.order) \
                          .update(order=models.F('order') - 1)

        self.order = to
        models.objects.filter(pk=self.pk).update(order=self.order)

    @classmethod
    def fix_order(cls):
        i = 0
        for obj in cls.objects.order_by('order').only('order'):
            i += 1
            obj.order = i
            obj.save()

