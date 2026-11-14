# Personal-detail removal: before and after

Generated 14 November 2026 from `examples/fake_whatsapp_chat.png` (all details invented).
Artist entered by the user: **Dave**.

## Before: what the reading model saw

```
Hi, still got the Dave tickets?
Yes 2 left, £85 each
Bank transfer only, PayPal
is down. Call 07123 456789
Can you do Twickets?
Sorry Jess, bank only
```

## After: what Step 2 receives

```
Hi, still got the Dave tickets?
Yes 2 left, £85 each
Bank transfer only, PayPal
is down. Call [phone]
Can you do Twickets?
[name], bank only
```

**Removed: 1 × phone number, 1 × name, 1 × top and bottom bars**

The report counts what was removed but never keeps the removed values.
