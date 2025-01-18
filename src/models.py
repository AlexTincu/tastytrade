from tortoise.models import Model
from tortoise import fields

class OptionsGreeks(Model):
    id = fields.BigIntField(pk=True)  # Unique primary key
    event_symbol = fields.CharField(max_length=50, index=True)  # For `.TSLA250221C360`
    # event_time = fields.BigIntField()  # Integer representation of time
    # event_flags = fields.IntField()
    index = fields.BigIntField()  # Unique index for events
    time = fields.BigIntField()
    sequence = fields.IntField()
    price = fields.FloatField()
    volatility = fields.FloatField()
    delta = fields.FloatField()
    gamma = fields.FloatField()
    theta = fields.FloatField()
    rho = fields.FloatField()
    vega = fields.FloatField()

    class Meta:
        table = "options_greeks"  # Define the table name
        indexes = ["event_symbol"]  # Optional: Composite index for queries

    def __str__(self):
        return f"OptionsGreeks(event_symbol={self.event_symbol}, price={self.price})"
