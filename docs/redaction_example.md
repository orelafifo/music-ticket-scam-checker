# Personal-detail removal: before and after

Generated 14 November 2026 from `examples/fake_whatsapp_chat.png` (all details invented).
Artist entered by the user: **Dave**.

## Before: what OCR read

```
Jess Smith
online
Hi, still got the Dave tickets?
14.32
Yes 2 left, €85 each
14.32
Bank transfer only, PayPal
14.32
is down. Call 07123 456789
14.32
Can you do Twickets?
14.32
Sorry Jess, bank only
14.32
Seen
Type a message
```

## After: what Step 2 receives

```
Hi, still got the Dave tickets?
Yes 2 left, €85 each
Bank transfer only, PayPal
is down. Call [phone]
Can you do Twickets?
[name], bank only
```

**Removed: 6 × timestamp, 3 × top or bottom bar text, 1 × app word, 1 × phone number, 1 × name**

The report counts what was removed but never keeps the removed values.
