# Generated by Django 4.1.5 on 2023-11-02 02:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitio', '0020_prestamos_prestamo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carrito',
            name='total',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]