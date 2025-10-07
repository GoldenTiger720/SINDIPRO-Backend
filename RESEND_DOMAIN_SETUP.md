# Resend Domain Verification Guide

## Why Domain Verification is Required

Without domain verification, Resend only allows sending test emails to the account owner's email address.
To send emails to any recipients, you must verify your domain.

## Step-by-Step Domain Verification

### 1. Access Resend Dashboard
- Go to: https://resend.com/domains
- Login with your Resend account

### 2. Add Domain
- Click **"Add Domain"**
- Enter: `sindipro.com.br`
- Click **"Add"**

### 3. Get DNS Records
Resend will provide DNS records to add. Example:

```
Type: TXT
Name: _resend
Value: resend-verify=abc123xyz456...
```

```
Type: TXT
Name: resend._domainkey
Value: p=MIGfMA0GCSqGSIb3DQEBAQUAA4...
```

### 4. Add DNS Records to Your Domain

**Option A: If you manage DNS yourself**
- Go to your DNS provider (Cloudflare, GoDaddy, AWS Route53, etc.)
- Add the TXT records provided by Resend
- Wait 5-10 minutes for DNS propagation

**Option B: If someone else manages DNS**
- Send these DNS records to your domain administrator
- Ask them to add these records to `sindipro.com.br`

### 5. Verify Domain
- Return to Resend Dashboard
- Click **"Verify"** next to your domain
- Wait for verification (may take a few minutes)

### 6. Update .env File

Once verified, update your `.env`:

```env
DEFAULT_FROM_EMAIL=Sindipro <noreply@sindipro.com.br>
```

Or use any email with your domain:
```env
DEFAULT_FROM_EMAIL=Sindipro <notifications@sindipro.com.br>
```

## DNS Verification Check

Check if DNS records are propagated:

```bash
# Check TXT record
dig TXT _resend.sindipro.com.br +short

# Check DKIM record
dig TXT resend._domainkey.sindipro.com.br +short
```

## After Verification

Once your domain is verified:
- You can send emails to ANY email address
- Use any `@sindipro.com.br` as sender
- No more restrictions on recipients

## Troubleshooting

**DNS not propagating?**
- Wait 10-30 minutes
- Check DNS records are added correctly
- Try flushing DNS: `sudo systemd-resolve --flush-caches`

**Verification failed?**
- Double-check DNS records match exactly
- Ensure no extra spaces in TXT values
- Contact Resend support if needed

## Alternative: Use a Different Verified Domain

If you don't have access to `sindipro.com.br` DNS, you can:
1. Register a new domain (e.g., `sindipro-notifications.com`)
2. Verify that domain instead
3. Use it as sender address
